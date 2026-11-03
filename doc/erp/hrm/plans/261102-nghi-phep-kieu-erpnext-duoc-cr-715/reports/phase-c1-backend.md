# Phase C1 (backend) duoc-CR-715 — Phiếu xin nghỉ bù — report

Migration: `lvcmp715` (down `lvblk715`), hand-written idempotent, applied local. Head = `lvcmp715`.
Permission entity: `leave_comp_request`, label "Nghỉ phép › Phiếu nghỉ bù". ENTITIES 78 → 79.
Router: `/api/leave-comp-requests` (registered in app/main.py before nothing conflicting; static `/to-approve` is declared before `/{rid}`).

## API contract
Envelope: `{success, message, data}` (core.response.success). Errors: `{success:false, error:{code,message,details}}` via global handler.
Auth entity for all: `leave_comp_request`. Scope = apply_scope/get_scoped (owner `created_by` + self `employee_id`, company, dept); out-of-scope id -> 404.
Exception: an approver with a pending approval task can GET (read) a request outside his scope (same as leave CR-260).

### Status enum `status` (SMALLINT, `LeaveCompStatus`, labels in `LEAVE_COMP_STATUS_LABELS`)
1 DRAFT "Nháp" · 2 PENDING "Chờ duyệt" · 3 APPROVED "Đã duyệt" · 4 REJECTED "Từ chối" · 5 RETURNED "Trả về chỉnh sửa" · 6 CANCELLED "Đã hủy".
Editable (PATCH/submit): 1, 5. Delete: only 1 (soft).

### Item shape (list rows, detail, and every mutation response)
`id, code ("NB001"), company_id, department_id, department_name, employee_id, employee_name, employee_code, work_date (YYYY-MM-DD), days (0.5|1), reason, status, status_label, approval_instance_id (0 = no running engine instance), decided_at, decision_note, created_by, created_at, updated_at`.
Detail (`GET /{id}`) adds: `created_by_name`, `has_running_approval` (bool; UI shows approval panel via existing `/api/approvals/of/leave_comp_request/{id}` when `approval_instance_id > 0` / `has_running_approval`).
`/to-approve` rows add `task` (my approval task, has `instance_id`) and `flow` (steps).

### Endpoints
| Method + path | Perm | Body / query | Result |
|---|---|---|---|
| GET `/api/leave-comp-requests` | read | `page`, `page_size`, `status`, `employee_id`, `company_id`, `department_id`, `q` (code / reason / employee name), `sort` via apply_sort_from_request; default sort work_date desc | `{total, items[]}` |
| GET `/api/leave-comp-requests/to-approve` | login (tasks of my employee) | - | `{total, items[]}` pending tasks for me |
| GET `/{id}` | read | - | item + extras; 404 if out of scope |
| POST `/api/leave-comp-requests` | create | `{employee_id?:0 (=me), work_date, days (0.5\|1, default 1), reason (<=1000)}` | item (DRAFT) |
| PATCH `/{id}` | write | `{work_date?, days?, reason?}` | item; 400 if not DRAFT/RETURNED |
| DELETE `/{id}` | delete | - | `data:null`; 400 if not DRAFT |
| POST `/{id}/submit` | write | - | item (PENDING); starts engine if switch on, else `approval_instance_id=0` and approve directly |
| POST `/{id}/approve` | approve | - | item (APPROVED); 400 if not PENDING or engine instance running; 403 self-approval when setting `leave_prevent_self_approval` on |
| POST `/{id}/reject?reason=` | approve | reason<=500 | item (REJECTED); same preconditions |
| POST `/{id}/cancel?reason=` | cancel | reason<=500 | item (CANCELLED); withdraws running instance first |

### Business errors
- 422 no comp type: "Chưa có loại nghỉ nào bật **Loại nhận ngày nghỉ bù**…" (active + is_compensatory + counts_balance, lowest sort_order).
- 422 `work_date` in the future; 422 working day (not holiday / not rest day by schedule); 422 days not in {0.5,1}; 422 reason empty at submit.
- 409 duplicate: another active (DRAFT/PENDING/APPROVED/RETURNED) request same employee + work_date.
- 403 creating for another employee without wider create scope / outside employee scope (reuses `request_service.ensure_can_create_for`, new optional arg `entity`).
- 422 cancel APPROVED when remaining of comp type for that year < days ("đã được dùng để nghỉ").

### Effects on balance
APPROVED (engine or direct): `tab_leave_balance.comp_days += days` for year = work_date.year, comp leave type (ensure_balance creates row). `total_days`/`remaining_days` include `comp_days`. REJECTED / RETURNED / withdrawn: no balance change. Cancel APPROVED: `comp_days -= days` (only if remaining >= days).

### Other API fields added
- LeaveType create/update/response: `is_compensatory: bool` (filterable on `/api/leave-types`).
- LeaveBalanceResponse: `comp_days: float` (already inside `total_days`/`remaining_days`).
- Balance report (`balance_report_spec`) granted/remaining now include `comp_days`.

## Files
New: leave/comp_request_model.py, comp_request_schema.py, comp_request_service.py, comp_approval_bridge.py, comp_request_controller.py; migrations/versions/lvcmp715_nghi_phep_phieu_nghi_bu.py; test/backend/test_nghi_phep_nghi_bu_cr715.py (27 tests).
Edited (backend): core/permissions.py, core/scoping.py, core/entity_models.py, core/all_models.py, seed.py (`_SYS_ENTITIES` +entity; setdefault own for all roles; dept_head dept+approve; company_head company+approve; hr_leave all), main.py (router + bridge import), approval/task_notification.py (label + link `/hr/leave-comp-requests/{id}`), approval/permission_approvers.py, approval/report_service.py, approval/self_approval_policy.py (`SELF_EXCLUSION_ENTITIES`), leave/balance_model.py, leave/catalog_model.py, leave/schema.py, leave/constants.py, leave/catalog_controller.py, leave/balance_report_spec.py, leave/request_service.py (`ensure_can_create_for(..., entity=)`), scripts/seed_help_nghi_phep.py (new article "Xin nghỉ bù", reseeded; reindex_help_rag NOT run).
Edited tests: scope_factory.py (entity->model map), test_pham_vi_khai_du_b07.py (78→79), test_duyet_theo_quyen_cr680.py (approver entity list), test_pham_vi_duong_vong.py (db.get whitelist; also back-filled 2+2 entries for phase A/B that were missing -> total 105).

## Tests
- New file: 27 passed. Matrix/scope/B07/duong_vong/luat_bat_bien/cr680 files: green after fixes.
- Filtered run: known failure `test_assistant_ai_duyet_phieu_kh_ai2_7::test_luong_nhieu_buoc_chi_nguoi_co_viec_cho` only. `test_po_submit_guard.py` HANGS in this container (unrelated PO test, hangs also without my change in the -k run order) — excluded.

## Deviations / notes
1. `entity_hooks` flow-designer: no explicit entity list exists backend-side; entity registers via `entity_hooks.register` + `permission_approvers._MODELS` + `ENTITY_LABELS`. C2 must add the entity to the frontend flow-designer/switch option list if one exists there. No seed flow / ApprovalSwitch row created (admin turns on in "Bật bộ máy duyệt"; off = direct approve).
2. D-018: running systems — existing roles do NOT get `leave_comp_request` automatically (seed_prod does not overwrite). Set `SEED_FORCE_SYNC=true` once or tick manually on Phân quyền (hr_leave / dept_head / company_head / employees "own").
3. Detail `has_running_approval` extra; no `submitted_at` column (not in spec).
4. Duplicate -> 409 (not 422); frontend should show message as is.
5. Working-day test uses `workday_service.count_leave_days(work_date, work_date) > 0` (half working day, e.g. Saturday morning, counts as working).
6. Fixed phase A/B whitelist drift in test_pham_vi_duong_vong (not caused by C).
7. Assistant (leave_tool) needs no change: uses `total_days` + `available_days` which include comp_days.

Unresolved: none blocking. Help RAG reindex not run. No frontend touched.

**Status:** DONE_WITH_CONCERNS (concerns: full filtered suite could not finish because unrelated test_po_submit_guard hangs; items 1-2 above)
