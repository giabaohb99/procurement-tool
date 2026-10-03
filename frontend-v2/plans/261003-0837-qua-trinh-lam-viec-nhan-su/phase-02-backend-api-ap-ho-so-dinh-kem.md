# Phase 02 — Backend: API, áp hồ sơ, đính kèm, /me

**Ưu tiên:** P2 · **Effort:** 5h · **Trạng thái:** completed · **Phụ thuộc:** 01

## Bối cảnh
- `employee/controller.py` (774 dòng — KHÔNG nhét thêm; router riêng): `_employee_in_scope`, `update_employee` + chốt L1/L2, `/me` (CR-378), `/me/contacts` (bao-CR-508).
- `employee/service.py`: `update_employee` (một giao dịch, `sync_label`, `detach_other_company_departments`, **`has_left_company` → `lock_linked_users`** = đường nghỉ việc SẴN CÓ của tab «Chung», bao-CR-400), `STATUS_RESIGNED = "resigned"`, `delete_employee`.
- `employee/field_limits.check_resign_after_hire` (nghỉ việc không trước ngày vào làm).
- `employee/department_service.py` (L1, L2, L3 trong `set_departments`, `set_extra_departments`).
- `employee/sensitive.can_read_sensitive(profile, employee_id)` (khóa `employee_sensitive.read` HOẶC chính chủ).
- `core/privilege_escalation.is_system_admin(db, user_id)`.
- `core/file_registry.py`, `core/attachment_scope.py` (`parent_records`), `attachment/controller.py` `_check`, `attachment/service.delete_attachments_for`.

## Tệp

| Tạo | Sửa (đúng chỗ, ít dòng) |
|---|---|
| `employee/work_history_schema.py` | `app/main.py` — include router mới **trước** `employee_router` |
| `employee/work_history_service.py` (đọc/ghi/validate/cảnh báo) | `core/file_registry.py` — `"employee_work_history": ("employee", _DOC, 50)` + `PRIVATE_ENTITIES` |
| `employee/work_history_apply_service.py` (áp hồ sơ) | `core/attachment_scope.py` — nhánh `parent_records` dòng → `Employee` (khuôn `_fk`) |
| `employee/work_history_access.py` (tự sửa, cờ quyền, `check_file`) | `attachment/controller.py` `_check` — ~6 dòng gọi `check_file` |
| `employee/work_history_controller.py` (prefix `/api/employees`) | `employee/service.py` `delete_employee` — dọn dòng + tệp |

Mỗi tệp mới < 200 dòng.

## Hợp đồng API (phase 04 code theo đây)

Envelope chuẩn. `hid` luôn kiểm `row.employee_id == eid`, lệch → 404 (chặn IDOR chéo người).

| Đường | Gác | Trả `data` |
|---|---|---|
| `GET /api/employees/me/work-history` | đăng nhập; id từ `user.employee_id` | `{items, can_edit:false, can_open_files:true}`; chưa gắn hồ sơ → `items: []` |
| `GET /api/employees/{eid}/work-history` | `employee.read` + `get_scoped(read)` 404 | `{items, can_edit, can_open_files}` xếp `from_date desc, id desc` |
| `POST /api/employees/{eid}/work-history` | `employee.write` + `get_scoped(write)` + chặn tự sửa | `{item, warnings[], applied_changes[]}` |
| `PATCH /api/employees/{eid}/work-history/{hid}` | như trên | như trên |
| `DELETE /api/employees/{eid}/work-history/{hid}` | như trên | `null` |
| `POST /api/employees/{eid}/work-history/{hid}/apply` | như trên | `{item, applied_changes[]}` |

`/me/...` khai **trước** `/{eid}/...`.

**Cờ (A9, tính ở `work_history_access`):** `can_edit` = có `employee.write` trên hồ sơ (scope write) VÀ (không phải hồ sơ của chính mình HOẶC `is_system_admin`). `can_open_files` = `can_read_sensitive(profile, eid)` (đã gồm chính chủ).

**`WorkHistoryOut`:** `id, employee_id, event_type, from_date, to_date, company_id, company_name, department_id, department_name, position_id, position_label, decision_no, decision_date, note, applied_at, file_count, is_current, can_apply`.
`file_count` luôn trả (kể cả khi `can_open_files=false` — Q4: vẫn báo «có tệp»; chỉ là SỐ, không lộ tên tệp). Tên + `file_count` gom một truy vấn mỗi loại cho cả danh sách. `is_current` = `to_date is None or to_date >= hôm nay VN`. `can_apply` = loại ∈ `APPLICABLE` và qua các chốt áp (không xét quyền).

**`WorkHistoryIn`** (`extra="forbid"`): `event_type` (∈ bộ mã, ≠0) · `from_date: ProfileDate` (= ngày hiệu lực, Q1) · `to_date: ProfileDate|None` · `company_id/department_id/position_id: int ≥0` · `decision_no: Str50` · `decision_date: ProfileDate|None` · `note: Str500` · `close_open_main: bool=False` · `apply_to_profile: bool=False`. `WorkHistoryUpdate` = cùng ô, tùy chọn hết.

## Validate (400/422)
1. `to_date >= from_date` (422).
2. Id công ty/phòng/chức vụ phải có thật (400); phòng + công ty cùng khai thì phòng phải thuộc công ty.
3. Kiêm nhiệm bắt buộc `department_id`; loại 1,2,3,5 bắt buộc ít nhất phòng hoặc chức vụ; Thôi việc không cần (bỏ qua ba ô nếu gửi 0).
4. Chức vụ đã ngừng dùng: cho ghi vào lịch sử; áp hồ sơ thì `sync_label` tự chặn gán mới.
5. Trần **200 dòng/người**.
6. Chồng lấn → **cảnh báo** trong `warnings`, không chặn (nhóm chính giao nhau; kiêm nhiệm cùng phòng giao nhau).
7. `close_open_main=True` (tạo dòng nhóm chính, kể cả Thôi việc): dòng chính đang mở có `from_date` sớm hơn → `to_date = from_date mới − 1 ngày`, cùng giao dịch, ghi audit.

## Áp vào hồ sơ (`work_history_apply_service.apply(db, row, actor, profile)`)

Gọi từ POST/PATCH (`apply_to_profile=True`) và `/apply`. Idempotent: hồ sơ đã khớp → `applied_changes=[]`, vẫn cập nhật `applied_at`.

Chốt chung (400, câu rõ): loại ∉ `APPLICABLE` · `from_date > hôm nay VN` («chưa tới ngày hiệu lực — quay lại bấm Áp khi tới ngày») · loại 1,2,3,5 mà dòng đã kết thúc (`to_date < hôm nay`) · loại nhóm chính (gồm Thôi việc) mà có dòng chính khác `from_date` muộn hơn.

| Loại | Làm gì | Đi qua |
|---|---|---|
| 1,2,3,5 | Đặt `company_id/department_id/position_id` — chỉ ô >0 và KHÁC hồ sơ | Phòng đổi: L1 + L2 (y hệt PATCH hồ sơ) → `service.update_employee(db, eid, EmployeeUpdate(**diff), actor.id)` |
| 4 Kiêm nhiệm | Đang hiệu lực → THÊM phòng kiêm nhiệm; đã kết thúc → GỠ phòng đó | L1 + L2 → `department_service.set_extra_departments(existing ± dept)` |
| 6 Thôi việc | `status = "resigned"` + `resign_date = row.from_date` (chỉ ô khác hồ sơ) | `service.update_employee(db, eid, EmployeeUpdate(status=…, resign_date=…), actor.id)` — **đúng đường tab «Chung»**: `has_left_company` bắt chuyển trạng thái → `lock_linked_users` (khóa TK, `force_relogin` thu hồi phiên, `perm_cache_clear`) + audit «khóa N tài khoản». KHÔNG gọi `lock_linked_users` trực tiếp, KHÔNG viết đường mới |

**Thôi việc — các ca ngày:**
- `from_date` = hôm nay hoặc trong quá khứ (nhập bù) → được áp; `resign_date` ghi vào hồ sơ = `from_date` của DÒNG (không phải ngày bấm). Khóa tài khoản xảy ra NGAY lúc áp, bất kể ngày nghỉ là ngày nào trong quá khứ.
- `from_date` tương lai (báo trước) → không hỏi, `/apply` trả 400; HR quay lại bấm «Áp vào hồ sơ» đúng ngày (A8 — không tác vụ nền). Tài khoản vẫn dùng được tới lúc đó.
- `resign_date < hire_date` → 400 (gọi `check_resign_after_hire(obj.hire_date, row.from_date)` trong apply — validator của `EmployeeUpdate` chỉ so khi payload có đủ hai ô).
- Hồ sơ đã «nghỉ việc» rồi: chỉ đổi `resign_date` nếu khác (không khóa lại — `has_left_company` chỉ bắt lúc CHUYỂN); khớp hết → no-op.
- `is_active` không đụng (tab «Chung» cũng không tự đổi khi chọn Nghỉ việc).

⚠️ **Một giao dịch:** service ghi dòng chỉ `flush`; nếu áp loại 1,2,3,5,6 thì `update_employee` commit MỘT lần cho mọi thứ đã flush (dòng lịch sử + `applied_at` + hồ sơ + khóa TK — `lock_linked_users` vốn không commit, nằm trong `try` của nó); không áp / kiêm nhiệm thì controller `commit`. `HTTPException` trước commit → phiên đóng không commit → dòng lịch sử cũng không còn.
⚠️ Không ghi thẳng `employee.position/department_id/status` — cấm đường ghi thứ ba.
⚠️ Chức danh kiêm nhiệm chỉ sống trong dòng lịch sử (`tab_employee_department` không có cột chức vụ).

## Quyền & IDOR
- Không entity mới → `ENTITIES`, `SCOPE_FIELDS`, b07, seed **không đổi**.
- **Chặn tự sửa (Q3):** mọi cửa ghi + gắn/gỡ tệp trên hồ sơ của chính mình → 403, **trừ** `is_system_admin(db, user.id)`. Tự thôi việc chính mình qua cửa này cũng vì thế bị chặn với người thường.
- `/me`: không tham số id; `employee_id = 0` → rỗng.
- **Tệp (Q4)** — `work_history_access.check_file(db, user, entity, entity_id, mode)` ở đầu `_check`, chỉ cho `entity == "employee_work_history"`:
  - đọc, dòng thuộc `user.employee_id` (≠0) → **qua** (không cần `employee.read`, không cần sensitive);
  - đọc, dòng người khác → `can_read_sensitive(profile, row.employee_id)` sai → **403**; đúng → rơi về luồng thường (`employee.read` + `ensure_in_scope` qua `parent_records`; ngoài phạm vi → 403);
  - ghi (gắn/gỡ), dòng của mình → 403 trừ quản trị; dòng người khác → cũng đòi `can_read_sensitive` (không cho gỡ/gắn tệp mà chính mình không được xem), rồi luồng thường (`employee.write` + phạm vi).
  Một chỗ phủ list/view/preview/download/remove.
- `PRIVATE_ENTITIES` ⇒ không trả `url` bucket.

## Audit
`record(db, actor, "employee", eid, action, msg, doc_code=emp.code)` sau commit. Mẫu: «Thêm quá trình công tác: Bổ nhiệm — Trưởng phòng KD, từ 01/10/2026, QĐ 12/QĐ-DG» · «Áp vào hồ sơ: phòng A → B; chức vụ X → Y» · «Áp thôi việc từ dòng quá trình công tác: nghỉ việc từ 30/09/2026» (dòng «khóa N tài khoản» do `update_employee` tự ghi) · «Đóng dòng … vào 30/09/2026».

## Xóa
- Xóa dòng: `delete_attachments_for(db, [("employee_work_history", hid)])` + xóa dòng, một commit. Không hoàn tác hồ sơ.
- `delete_employee`: dọn mọi dòng + tệp của người đó.

## Todo
- [x] schema (+ validator, forbid)
- [x] service đọc (gom tên + file_count + cờ), ghi, cảnh báo, close_open_main, trần 200
- [x] apply service: chính / kiêm nhiệm / thôi việc + chốt ngày
- [x] access: chặn tự sửa (trừ quản trị), cờ, `check_file` (+ sensitive) + nối `_check`
- [x] file_registry + PRIVATE + parent_records
- [x] controller + main.py; `delete_employee` dọn
- [x] gọi thử qua `/docs` local (xác nhận qua `app.main.app` — bốn route `work-history` đăng ký đúng; xem report)

## Thành công khi
Hợp đồng API đúng bảng trên; áp lỗi giữa chừng không để lại dòng; thôi việc khóa TK đúng như tab «Chung»; tệp người khác thiếu sensitive → 403.

## Rủi ro
| Rủi ro | K × A | Giảm thiểu |
|---|---|---|
| Commit sớm làm vỡ «một giao dịch» | TB × Cao | Không commit trước `update_employee`; test ép lỗi |
| Thôi việc nhầm người → khóa TK ngay | Thấp × Cao | Hộp xác nhận riêng ở FE; audit; mở lại TK là thao tác tay sẵn có ở tab Tài khoản |
| Áp dòng cũ đè hồ sơ hiện tại | TB × Cao | Chốt «dòng chính mới nhất» |
| Đổi phòng qua cửa này né L1/L2 | Thấp × Cao | Gọi đúng hai hàm chặn; test |
| Lộ tệp QĐ (có thể ghi lương) | Thấp × Cao | Riêng tư + sensitive + test |

## Rollback
Gỡ include router ở `main.py`, bỏ dòng `FILE_POLICY`, revert nhánh `_check`. Thay đổi hồ sơ đã áp là sửa hồ sơ bình thường — tra audit/`tab_change_log` để hoàn tay; tài khoản bị khóa mở lại ở tab «Tài khoản».
