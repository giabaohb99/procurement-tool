# Code review: duoc-CR-680, approver kind 9 «Người có quyền duyệt (theo phân quyền)»

## Scope
- Backend: `approval/permission_approvers.py` (new), `flow_model`, `approver_resolver`, `flow_controller`, `preview_service`. Test: `test/backend/test_duyet_theo_quyen_cr680.py`.
- FE: approval types/api/hooks/helpers/node-form/permission-approvers-hint, query-keys, plus the unrelated `hr/change-request-families-diff.tsx`.
- Gates run: backend CR-680 suite **16 passed** · vitest `src/modules/approval` **105 passed** · eslint on the touched files: 0 · `tsc --noEmit`: 0.
- Probes: a throwaway pytest in the container's `/tmp`, now deleted. It confirmed 4 bugs (C1, C2, H1, H2).

## Overall
The structure is clean: a small resolver, the ref is forced on the server, and the exclusions are documented. But the row-scope check (`get_scoped(..., "approve")` on the user's FULL profile) is the wrong primitive in 3 ways, and one routing bug sends approvals to the wrong table. All are confirmed with probes.

## Critical

**C1. Admin role's "all" scope leaks back through `get_scoped` (CONFIRMED)**
- `holders()` drops the `admin` role only from the *who qualifies* query. Then `resolve()` calls `get_scoped(..., get_perm_profile(db, user), "approve")`, and `scope_condition` ORs EVERY grant with approve, admin's `all` included.
- Probe: user = admin + `booking_dispatcher` scope=company, company 3. A booking in company 5 is resolved to `[that user]` (expected `[]`).
- Effect: any admin who also holds one approve role becomes approver of every ticket in the group. That is the exact outcome the docstring says it prevents.
- The same root cause brings back scope «own». Probe: dispatcher (company 3) + base role with approve scope=own, who created a booking for company 5 on someone's behalf, gets assigned. `exclude_submitter_ids` only drops `started_by_employee_id`, not `created_by`.
- Fix: run the scope check on a profile filtered down to the qualifying grants:
  ```python
  qual = {**profile, "grants": [g for g in profile["grants"]
          if g["role_id"] != admin_id
          and (g["perms"].get(entity) or {}).get("approve")
          and (g["perms"].get(entity) or {}).get("scope") != "own"]}
  get_scoped(db, model, entity, rid, user, qual, "approve")
  ```
  Add a test for admin + company-scoped role on a booking from another company.

**C2. Changing a flow's entity leaves kind-9 nodes pointing at the old table, so the scope check reads the WRONG ROW (CONFIRMED)**
- `FlowIn.entity` is editable through `PATCH /approval-flows/{id}` (`update_flow` uses setattr over every field). Nodes are not touched, so `approver_ref` keeps the old entity, and the snapshot copies it.
- `resolve()` then does `model_of(ref)` + `get_scoped(model, subject["id"])`, which means a VehicleBooking lookup using a SealRequest id.
- Probe: node ref `vehicle_booking`, seal request id=1 of company 9, vehicle booking id=1 of company 3. The company-3 dispatcher gets the company-9 seal approval.
- Fix (pick one or both):
  - In `update_flow`, when `entity` changes, rewrite `approver_ref` on its kind-9 nodes, or reject the entity change while kind-9 nodes exist (422).
  - Better: pass the instance entity (`instance.entity`) to the resolver, or put `"entity"` into the subject, and use that instead of trusting `approver_ref`.

## High

**H1. Document entity: the kind-9 scope check bypasses DENY rows and the personal-document gate, and the approver exemption then opens the doc**
- For `document`, `get_scoped(Document, "document", ..., "approve")` only checks role scope (company/dept/owner).
- `access_service.can()` returns True through `approving_this_document()` BEFORE it evaluates `DocumentAccess` CẤM rows (l.384 vs l.388) and BEFORE `_is_personal_document` (leave-request style personal docs).
- So a person explicitly denied on a document, or a company-scoped approve holder on someone's personal document, gets auto-assigned and can then read it.
- Folder ACL (`tab_doc_folder_access`) is not consulted either. Not verified whether `can()` reaches it further down; listed under questions.
- With kinds 1–8 the flow designer names people explicitly. Kind 9 fans out automatically, so this becomes systemic.
- Fix: for `document`, also require `access_service.can(db, doc, user, profile, "read")` (and `"approve"` if that column exists). No task exists yet at resolution time, so the approver exemption does not mask the check. Alternatively block kind 9 for `document` until this is decided.

**H2. seal_request: company-scope approve holders are never matched while the ticket is pending (CONFIRMED)**
- `_role_scope_cond` for `seal_request` + `company` ANDs `status IN (APPROVED, COMPLETED)`. For Văn thư it also requires a `tab_seal_clerk` assignment.
- During approval the ticket is `SEAL_PENDING`, so `get_scoped` returns None. Probe: a company-3 Director with seal approve scope=company on a company-3 PENDING seal request resolves to `[]`.
- Meanwhile `holder_profiles` / the FE hint list them as «Giám đốc · Công ty», and the hint text promises «phạm vi Công ty chỉ nhận phiếu của công ty mình». The step silently resolves to nobody, then `on_no_approver` takes over (stop or fallback).
- Same class of issue on vehicle_booking: `assigned`/`proc`/`dept_proc` reduce to created_by or the assigned driver, so they never match a fresh ticket but are still listed.
- Fix: per entity, document which scopes can resolve at approval time. Exclude non-resolvable scopes in `_approve_grant_conds`, or mark them in `holder_profiles` («không nhận được phiếu đang chờ duyệt»). Add a seal test.

## Medium

**M1. No subject id falls open to ALL holders (document preview)**
- The only preview callers are document flows (`document/approval_preview_controller.py`) and `assistant/tools/document_tool.py`, and both pass a subject without `id`.
- Result: the preview lists every approve holder in all companies. That is misleading (the real run filters by company), and it hands employee names and codes from other legal entities to anyone with `document.create`. M3 hardening restricted `company_id` in that preview precisely to stop this.
- The test `test_khong_co_id_phieu_thi_khong_loc_pham_vi` locks the fail-open behaviour in.
- Fix: when there is no id, return `[]` with an `unresolved_reason` such as "Tính theo phân quyền lúc gửi duyệt" (preview_service already has the `pending_field` pattern). A cheaper option is to approximate with `subject["company_id"]` against grants whose scope is all/company.

**M2. A model missing from `_MODELS` also falls open**
- Today every entity that calls `instance_service.start` is in the map: vehicle_booking, seal_request, document, room_booking, leave_request. So this is latent.
- The next module that gets a bridge without a `_MODELS` line silently assigns to every holder regardless of company. That is the opposite of the B-07 «thiếu khai = CHẶN» rule.
- Fix: return `[]` and log an error. Add a test that every entity with `entity_hooks.register_subject` is in `_MODELS`, or derive the model from the bridge registry. `purchase_request` is in `_MODELS` but has no bridge; harmless.

**M3. `/permission-approvers` leaks across companies and entities**
- It is gated only by `approval_flow.read`. It does not apply `approval_flow`'s own company scope, and it accepts ANY key in `ENTITIES`, so the caller can ask who holds approve on `employee`, `labor_contract`, and so on.
- It returns employee code, name, role names and scopes, which is role-assignment data normally behind `role.read`.
- Fix: accept only entities that have a bridge (`_MODELS` keys). Optionally require `approval_flow.write` (only flow editors need it), or filter holders by the caller's company reach.

**M4. Query fan-out**
- Each `resolve` costs 4 queries in `holders`, plus per holder a cold `get_perm_profile` (about 6–8 queries: UserRole, Permission, UserScope, emp_to_user, dept map, Employee, departments_of) and 1 `get_scoped`, plus 3 in `_only_active_employees`.
- With 20 holders that is about 150–200 queries inside the submit/approve transaction while the row lock is held. `flow_sync_service` repeats it for each running instance at that stage whenever a node is edited.
- Fine for about 100 users today, but worth capping. One option: group holders by (role set, UserScope) signature and evaluate once per signature. Another: build one `or_(...)` per holder and run a single `SELECT id ... WHERE id=:rid AND (...)` per batch.

## Low
- Approvers are a snapshot taken when the stage opens. Revoking approve afterwards does not cancel pending tasks; the engine never re-checks permission at decision time. This matches the other kinds; the FE hint states it ("phiếu mới tự theo").
- `holder_profiles` calls `system_admin_role_id` twice, via `holders` and directly. Trivial.
- `_rule_label` uses `task_notification.ENTITY_LABELS`. That covers all bridged entities today; `core/permissions.ENTITY_LABELS` would be the fuller source.
- `usePermissionApprovers(entity, true)`: the `enabled` argument is always true. YAGNI.
- `change-request-families-diff.tsx`: dropping `useMemo` is fine. `sides` is not a hook dependency; `rows` is now rebuilt every render. Low impact.

## Edge cases checked
- Submitter is also a holder: excluded by `exclude_submitter_ids`; tested.
- One employee with several users: deduped by `_only_active_employees`; tested.
- Default `multi_mode` = ANY (FE), so a fan-out to N holders does not demand every signature. With ALL/SEQUENTIAL it would. Consider warning or forcing ANY for kind 9.
- `flow_sync_service._rebuild_tasks`: kind 9 recomputes holders on any node edit (rename, SLA). If permissions changed, pending tasks get rebuilt. That is acceptable and consistent with CR-114.
- FE `flow-node-card` `CAN_REF` and `serializer.approver_names` do not need kind 9 (ref is forced server-side; the card falls back to the kind label). `references.py` needs nothing.
- The leave_request `self` column is only used by the own branch, which is excluded. dept/company work through `company_id`/`department_id`. OK, once C1's own-union is fixed.

## Positives
- Server overwrites `approver_ref`, so the client cannot redirect it to another entity at save time.
- Account active + employee_id>0 + employee active filters are consistent with the CR-398 two-sided check.
- `holder_profiles` uses a fixed number of queries; tests are real SQLite, not mocks.

## Recommended actions (in order)
1. C1: filtered-grant profile in `resolve` + test (admin+company role; own+created_by).
2. C2: use the instance entity instead of `approver_ref`, or resync/block in `update_flow` + test.
3. H1: check document access (deny/personal) for `document`, or disable kind 9 there.
4. H2: decide per-entity resolvable scopes; fix the hint copy; seal test.
5. M1/M2: fail closed for no id / unknown model; adjust the test that codifies fail-open.
6. M3: restrict the endpoint's entity whitelist and permission.

## Unresolved questions
- Is kind 9 meant to be offered for `document` at all, given folder ACL, secrecy level and personal docs? Does `access_service.can` consult `tab_doc_folder_access`? Not traced.
- seal_request: is kind 9 meant to target the TBP stage (dept-scope holders) or the Văn thư stage? The latter can't resolve while PENDING under the current scope rules.
- Should a flow's entity be editable once it has nodes at all? C2 suggests blocking it is the simpler rule.

**Status:** DONE_WITH_CONCERNS
**Summary:** Feature works for the happy path and all gates are green, but there are 2 confirmed critical routing bugs (admin/own grants leak into the scope check; a stale ref after a flow entity change reads the wrong table), 1 high security gap on documents, and seal company-scope holders that never resolve.
