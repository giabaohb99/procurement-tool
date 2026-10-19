# Pha 03 — Adapter Nhân sự mới (cột · parse · ghi qua service · hoàn tác)

**Ưu tiên:** P1 · **Trạng thái:** pending · **Công:** 1.25d · **Chặn bởi:** 01, 02

## Tệp
- Tạo `backend/app/modules/import_tool/employee_import_fields.py` (~180 dòng): bộ cột + bộ parse ô.
- Tạo `backend/app/modules/import_tool/employee_import.py` (~200 dòng): `prepare` / `apply_row` /
  `finalize` / `revert` / `revert_blockers`.
- Sửa `catalog_import.py`: mục `ADAPTERS[ImportModule.EMPLOYEE]` trỏ sang `fields` + hook của 2 tệp trên,
  `allow_delete=False`, `template_action_col=False`, `max_rows=2000`.
- Sửa test cũ `test/backend/test_import_catalog.py`: `test_nhan_su_khong_tao_tai_khoan_dang_nhap` dùng
  fixture `seed` + `created_by` = admin (lô Nhân sự nay cần người tạo có quyền).

## Bộ cột (tiêu đề mẫu · alias tương thích · kiểu)
Một nguồn: `EMPLOYEE_FIELDS`. Cờ **S** = thuộc `sensitive.SENSITIVE_FIELDS` (tính bằng
`attr in SENSITIVE_FIELDS`, KHÔNG gõ tay danh sách thứ hai).

| Nhóm | Tiêu đề (alias) | attr | Kiểu |
|---|---|---|---|
| Định danh | `Mã NV *` (Mã nhân viên) | code | khóa |
| | `Họ tên *` | full_name | str (bắt buộc khi TẠO) |
| | `Email` · `Điện thoại` (Số điện thoại) · `Email cá nhân` | email, phone, personal_email | str |
| | `Giới tính` · `Tình trạng hôn nhân` · `Trình độ học vấn` | gender, marital_status, education_level | mã số (nhận số hoặc nhãn) |
| | `Ngày sinh` **S** · `Nơi sinh` · `Dân tộc` · `Tôn giáo` · `Số con` · `Chuyên ngành` | … | date/str/int |
| Công việc | `Công ty (mã)` | company_id | ref công ty: mã → tên/MST (`resolve_ref_obj`) |
| | `Phòng ban (mã)` (Phòng ban) | department_id | ref PB: **mã chính xác**; lùi về tên CHÍNH XÁC trong đúng công ty, >1 khớp = lỗi |
| | `Chức vụ (mã/tên)` (Chức vụ, Vị trí) | position_id | `JobPosition.code` chính xác → `position_service.resolve_by_name`; không khớp = REVIEW, giữ chữ ở `position`, `position_id` không đổi |
| | `Quản lý trực tiếp (mã NV)` | manager_id | ref NV theo **mã** chính xác |
| | `Hình thức nhân viên` · `Cấp bậc` | employment_type, job_level | mã số |
| | `Nơi làm việc` · `Ngày vào làm` · `Ngày nghỉ việc` | work_location, hire_date, resign_date | str/date |
| | `Trạng thái` (Trạng thái NS, Trạng thái (official/probation/…)) | status | `status_code_from_text` (mã hoặc nhãn, bỏ dấu); sai = lỗi |
| | `Đang dùng (1/0)` (Hoạt động (1/0)) | is_active | bool; giá trị lạ = lỗi |
| Địa chỉ | `Địa chỉ thường trú` **S** · `Địa chỉ hiện tại` **S** | | str |
| Ngân hàng | `Số tài khoản` **S** · `Tên chủ tài khoản` **S** · `Ngân hàng` **S** · `Chi nhánh` **S** | bank_* | str |
| Giấy tờ | `Số CCCD` **S** · `Ngày cấp CCCD` **S** · `Nơi cấp CCCD` **S** · `Ngày hết hạn CCCD` **S** · `Số BHXH` **S** | id_*, social_insurance_no | str/date |
| | `Nơi KCB BHYT` · `Mã KCB BHYT` | health_care_* | str |

Ngoài phạm vi (YAGNI, ghi rõ ở sheet «Huong dan»): ảnh CCCD, `extra_fields`, `role_name`, người báo
tin/gia đình, kiêm nhiệm, tạo tài khoản đăng nhập.

## Luật ô (sửa rủi ro #2)
- Cột vắng hoặc ô **trống** → KHÔNG đưa vào `fields` (giữ nguyên). Tạo mới: trống = mặc định schema.
- Ô = `__/empty_value/__` → xóa: str `""`, date `None`, mã số/ref `0`. Riêng `full_name`, `status`,
  `is_active` → lỗi dòng «không xóa được ô bắt buộc».
- Ngày: nhận `datetime/date` của openpyxl, chuỗi `dd/mm/yyyy` hoặc `yyyy-mm-dd`; sai = lỗi dòng.
  Dải năm do `ProfileDate`/schema chặn.
- Mã số: số nguyên trong `*_LABELS` hoặc nhãn (so bỏ dấu, hoa thường). Sai = lỗi dòng, nêu giá trị nhận.

## `prepare(ctx)` — một lần mỗi lô
`user = db.get(User, batch.created_by)`; không có/đã khóa → `ImportValidationError`. `profile =
get_perm_profile`. `can_create/can_write = perms_union.employee.create/write`. `sensitive_ok =
perms_union.employee_sensitive.write`. Nếu file có cột **S** mà `not sensitive_ok` → loại các cột đó khỏi
`field_col` + 1 log WARNING dòng 0 `sensitive_ignored`: «Bạn không có quyền ghi thông tin nhạy cảm —
bỏ qua các cột: …» (chỉ tên cột).

## `apply_row` — thứ tự
1. Parse → `fields` (dict). Lỗi parse → ERROR, dừng dòng.
2. `existing = Employee.code == code` (code trống → tạo mới, mã NSU tự sinh bởi lõi).
3. Có `existing`: thiếu `can_write` → lỗi; `get_scoped(..., "write") is None` → lỗi
   «Mã NV '{code}' không ghi được (ngoài phạm vi dữ liệu của bạn)» — KHÔNG tạo bản trùng.
   Không có: thiếu `can_create` → lỗi; thiếu `full_name` → lỗi.
4. Phòng ban đổi thật: `block_edit_own_department` (L1, chỉ khi sửa) + `block_out_of_scope_departments` (L2).
5. Dựng `EmployeeUpdate(**fields)` / `EmployeeCreate(**fields)` — `ValidationError` → lỗi dòng ghép từ
   `loc` + `msg` qua nhãn cột, **KHÔNG kèm `input`** (tránh lộ giá trị nhạy cảm vào log). Đây là chốt
   độ dài `Str*` (rủi ro #6) và chốt bộ mã.
6. Sửa: so `fields` với giá trị hiện tại → không khác → `unchanged` (INFO, không `ImportChange`).
7. `snapshot` = **mọi attr của `EMPLOYEE_FIELDS` + `position`** của `existing` TRƯỚC khi ghi (rủi ro #4).
8. `with db.begin_nested():` gọi `update_employee_core(..., lock_users=apply)` / `create_employee_core`;
   sau flush `get_scoped(..., "write")` phải còn thấy bản ghi, không thì raise → savepoint lùi → lỗi
   «sau khi ghi hồ sơ nằm ngoài phạm vi của bạn». `HTTPException`/`ValueError` → lỗi dòng (`detail`).
9. `left_company` & dry-run → WARNING «Sẽ khóa tài khoản đăng nhập của {code} khi ghi thật».
10. Gom vào `ctx.after`: `(eid, "create"|"update", notes, scope_changed, locked_user_ids)`.

Quản lý ở dòng SAU trong cùng tệp: không thấy → lỗi «đưa dòng người quản lý lên trước». Không làm 2 lượt (YAGNI).

## `finalize` (chỉ apply, sau commit)
Mỗi phần tử `ctx.after`: `record(db, actor, "employee", eid, action, "Nhập Excel lô #{batch.id}; " + notes)`;
`record(... "user", uid, "deactivate", ...)` cho TK bị khóa; `clear_perm_cache_of` nếu `scope_changed`.

## Hoàn tác
- `revert_blockers`: bản ghi MỚI → `reference_guard.ensure_deletable` +
  `labor_contract_service.ensure_employee_deletable` + có `User.employee_id` trỏ tới → gom câu chặn
  (mã + lý do), từ chối cả lượt. Bản ghi CŨ: không chặn.
- `revert`: MỚI → `delete_employee_core`; CŨ → parse snapshot (ngày ISO → `date`) →
  `EmployeeUpdate.model_construct(**snap)` (bỏ validate: khôi phục trạng thái DB cũ, dữ liệu cũ có thể
  không qua luật mới) → `update_employee_core(lock_users=False)` → giữ đồng bộ phòng chính/nhãn CV.
  Sau commit: `clear_perm_cache_of` cho người đổi phạm vi.
- ⚠️ Hoàn tác KHÔNG mở lại tài khoản đã khóa (đúng luật bao-CR-400: «quay lại làm» là quyết định tay).
  Ghi rõ trong câu trả về.

## Todo
- [ ] `employee_import_fields.py`: `EMPLOYEE_FIELDS`, parse ngày/mã số/bool, `template_notes`
- [ ] `employee_import.py`: prepare / apply_row / finalize / revert / revert_blockers
- [ ] Nối `ADAPTERS[EMPLOYEE]`
- [ ] Sửa `test_nhan_su_khong_tao_tai_khoan_dang_nhap`
- [ ] Viết test mới (pha 06 liệt kê) song song với code

## Thành công khi
Test `test_nhap_excel_nhan_su_cr628.py` + `test_nhap_excel_nhan_su_quyen_cr628.py` xanh; log không chứa
giá trị cột **S** (test quét `ImportLog.message`).

## Rủi ro
| Rủi ro | K×T | Giảm thiểu |
|---|---|---|
| Savepoint + `set_departments` lỗi giữa chừng để lại trạng thái bẩn | TB×Cao | Mọi ghi trong `begin_nested`; test lỗi giữa dòng → dòng sau vẫn đúng |
| Dry-run gọi dịch vụ AI / đá phiên thật | TB×Cao | `lock_users=apply`; test dry-run nghỉ việc → `User.is_active` không đổi |
| Tên phòng ban trùng giữa pháp nhân | Cao×TB | Ưu tiên mã; tên chỉ trong đúng công ty, >1 = lỗi |
| `tab_import_change.snapshot` giữ bản rõ CCCD/STK | Chắc×TB | Không có API nào đọc bảng này (đã rà controller); ghi vào luật HR; câu hỏi treo về dọn snapshot |
| SQLite không ép `VARCHAR` → test xanh giả | Cao×TB | Test độ dài khẳng định ERROR log từ tầng schema, không đọc DB |
