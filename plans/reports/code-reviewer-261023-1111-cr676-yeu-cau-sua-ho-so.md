# Code review — duoc-CR-676 (HR2-2) yêu cầu sửa hồ sơ nhân sự

## Scope
- Backend: `employee/change_request_{model,schema,service,view,controller}.py`, `core/hr_change_request_codes.py`, diffs `all_models/code_sets/change_tracker/logging_policy/main.py`, `employee/contact_service.py`, migration `cr676chgreq01`, test `test_yeu_cau_sua_ho_so_cr676.py`
- Frontend-v2: hr change-request + print files, router/print-route-access, app-routes, query-keys, statuses.ts, profile-page, employee-detail-page, people-editor, tab-documents, reason-confirm-dialog
- Checks run: pytest cr676 + pham_vi_duong_vong + cr538 = **103 passed**; `alembic heads` = single `cr676chgreq01`, live DDL matches model; `tsc` 0 errors; eslint (touched dirs) 0 errors / 2 pre-existing warnings; vitest (4 new test files + `src/app/router`) **133 passed**

## Overall
Solid. Permission model right (write-scope 404, self-approve block, sensitive gate), extra=forbid on every group, masking at serializer + change_log + request_log, approve is one transaction with rollback, approve/reject double-decision serialized by `refresh(with_for_update=True)`. No Critical. Issues are state-machine races and stale-overwrite.

## Critical
None.

## High / Medium

### M1. Withdraw overwrites an already APPROVED/REJECTED request (race) — `change_request_controller.py:104-113`
`_own_request` = plain `db.get` (RR snapshot) → status check → `decide(WITHDRAWN)`. Approve holds `FOR UPDATE`; withdraw's UPDATE blocks, then runs `UPDATE ... SET status=4 WHERE id=?` on the latest row after approve commits. Result: profile already changed, request shows «Đã rút lại», `decided_by` = employee. Approve/reject are safe; withdraw is the only unlocked transition.
Fix (either):
```python
req, emp = _own_request(db, rid, user)
db.refresh(req, with_for_update=True)          # locking read sees latest committed status
if req.status != int(Status.PENDING): raise HTTPException(409, ...)
```
or conditional update: `db.query(Req).filter(Req.id == rid, Req.status == 1).update({...})`, rowcount 0 → 409.

### M2. Two PENDING requests possible (check-then-insert, no lock) — `change_request_controller.py:89-97`, `change_request_service.py:115`
`pending_of` plain SELECT then INSERT. Two tabs / two devices / retry → both pass → 2 pending (frontend `submittingRef` only guards one dialog instance). Model doc promises "tối đa MỘT". Note: per repo memory, locking `Employee` then plain SELECT is NOT enough on RR (snapshot already fixed by `get_current_user`).
Fix (robust): nullable unique column `pending_employee_id BIGINT NULL UNIQUE` = `employee_id` while pending, set NULL in `decide()`; catch `IntegrityError` → 409. Cheaper: lock emp row `with_for_update()` AND make `pending_of` a locking read (`.with_for_update(read=True)`).

### M3. Approve silently overwrites families edited by HR after submission — `change_request_service.py:86-88`, `change_request_view.py:69-72`, `change-request-families-diff.tsx`
`set_families` replaces the whole list with `after`. Scalar items expose `current` + highlight, families do not (only «Lúc gửi» vs «Đề nghị»). HR edits family via `PUT /{eid}/families` after submit → approver sees nothing → edit lost.
Fix: in approve (after lock) `if req.families and svc.current_families(db, emp.id) != req.families["before"]: raise HTTPException(409, "Hộ gia đình đã đổi sau lúc gửi — từ chối và nhờ gửi lại")`; or add `current` to serialized families and highlight. Consider same 409 for scalar fields where `current != before` (confirm dialog already warns, so optional).

### M4. Families load error → empty editor → request deletes existing members — `self-change-request-dialog.tsx:124-127,185-188`, `self-change-request-card.tsx:42,145`
If `/me/families` errors, `families=undefined`, `isLoading=false` → editor renders empty; user adds 1 row → `after=[new]` vs baseline `[]` → sent; on approval all real members are wiped (backend `before` shows them, but easy to miss).
Fix: pass `families.isError`; disable the «Hộ gia đình» tab / show ErrorState; in `handleSubmit` refuse when `familiesDraft !== null && families === undefined`.

## Low
- L1 `employee-pending-change-request-banner.tsx:25-31`: `q=code` LIKE substring + `page_size 5` — NSU001 matches NSU0010…NSU0019; ≥5 pending matches can hide the real one. Add `employee_id` filter to `GET /change-requests` and use it.
- L2 `change_request_schema.py:27`, `change_request_service.py:82-84`: nested `EmployeeUpdate.model_validate` error is stringified (`input_value=…`, pydantic docs URL) into 422 `msg` / 400 message. Only int codes today, but brittle + ugly. Catch `ValidationError` and re-raise `ValueError(exc.errors()[0]["msg"])`.
- L3 `use-employee-change-requests.ts:94-100`: after approve, `myEmployee` / `myChangeRequests` not invalidated (admin approving own request sees stale /me). Add both.
- L4 File size >200: `self-change-request-dialog.tsx` 228, `profile-change-request-detail-page.tsx` 240 (split form body / action bar).
- L5 Audit uses action `update` on employee for submit/withdraw/reject though profile unchanged — timeline reads «Cập nhật». Consider distinct wording/action.
- L6 `list_change_requests` LIKE does not escape `%`/`_` — cosmetic.

## Verified OK (scout)
- IDOR: `/me/change-requests/{rid}/withdraw` checks `employee_id == user.employee_id` (404); HR list/count use `apply_scope(..., "write")` on joined Employee; detail/approve/reject via `get_scoped(..., "write")` → 404.
- Mass assignment: every group `extra="forbid"`; `changes` built server-side from allowlisted fields only; no `email/department/position/status` reachable → no scope change, no perm-cache clear needed, no self-escalation path.
- Atomicity: `update_employee_core` + `set_families` only flush; single commit; rollback on any exception (test covers).
- Masking: serializer hides `before/after/current` per `SENSITIVE_FIELDS`, families null when masked; change_log allowlist row-level only; request_log masks nested sensitive keys + `families`; 2xx response summarized to ids; notifications carry group labels only; print page uses masked `GET /employees/{id}` and gates sub-tables on `useCanReadSensitive`.
- Migration: single head, only create table + 2 indexes, applied DDL matches model.
- Routing: change-request router included before `employee_router`; nav item `employee.write` gates `/hr/profile-change-requests/*`; print routes declared in `PRINT_ROUTE_ACCESS`.
- Status R2: SMALLINT + IntEnum, generated TS set, FE constants only name numbers.

## Recommended actions
1. M1 lock in withdraw (2 lines).
2. M2 unique pending key (or locking-read pair).
3. M3 409 on stale families (+ optional scalar).
4. M4 block families tab on load error.
5. L1-L3 small follow-ups.

## Unresolved questions
- Approve of sensitive fields requires `employee_sensitive.read` only; CR-628 import requires `employee_sensitive.write` for the same columns, PATCH requires neither. Intended policy?
- Users holding `employee.write` scope `own` can still PATCH their own profile directly, bypassing this approval flow (pre-existing). Accept?
- No notification to HR on new submission (badge only, 60s stale) — intended?

**Status:** DONE_WITH_CONCERNS
**Summary:** No critical issues; 4 medium (withdraw race, double-pending race, stale families overwrite, families-load-error data loss) + minor follow-ups.
