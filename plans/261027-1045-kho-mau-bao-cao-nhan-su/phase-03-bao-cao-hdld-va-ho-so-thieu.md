# Phase 03 — B1 Hợp đồng lao động + E1 Hồ sơ & tài khoản còn thiếu

**Ưu tiên:** cao · **Trạng thái:** done (27/10/2026) · **Chủ:** BE-2 · **Phụ thuộc:** 01
**Tài liệu:** `doc/erp/hrm/05-bao-cao-nhan-su.md` B1, E1

## Chủ tệp
`backend/app/modules/labor_contract/report_*.py` (mới) · `backend/app/modules/employee/profile_gaps_report_*.py` (mới) · `backend/app/main.py` (chỉ include 2 router mới, TRƯỚC router chính của phân hệ) · `test/backend/test_phan_quyen_bao_cao_gac_duong.py` (thêm 4 đường vào `GATED` + `ROUTE_SPECS`) · `test/backend/test_bao_cao_hdld_cr686.py`, `test_bao_cao_ho_so_thieu_cr686.py` (mới).

## B1 — `GET /api/labor-contracts/summary` (+ `/export`, `/rows`) · khóa 17 · `require('labor_contract', read|export)`
- Phạm vi: `apply_scope(LaborContract, "labor_contract")` + `not_deleted_cond`; người chưa có HĐ đọc qua `apply_scope(Employee, "employee")`.
- `as_of = min(cuối kỳ, hôm nay)` (`vn_today()`); kỳ so sánh tính lại tại `compare_to` của nó.
- Hàng = mỗi HĐ (cờ trạng thái) + mỗi nhân sự đang làm chưa từng có HĐ đã ký. Chỉ số đếm cờ (không `snapshot`) để có ở cả Tổng lẫn nhóm; `trend = []` (giao diện ẩn biểu đồ).
- Chỉ số:
  - `active` «Đang hiệu lực»: SIGNED, `start_date ≤ as_of`, `end_date` trống hoặc `≥ as_of`, **người còn làm** (chốt 27/10).
  - `resigned_not_terminated` «Người đã nghỉ, HĐ chưa chấm dứt»: như trên nhưng người đã nghỉ — để Nhân sự dọn sổ (thêm 27/10).
  - `expiring_30` / `expiring_60` / `expiring_90` «Hết hạn trong 30/60/90 ngày»: đang hiệu lực, `end_date ∈ [as_of, as_of + N]` (gồm cả HĐ hết đúng hôm nay — chốt 27/10), chưa có HĐ nối tiếp, người còn làm (luật ở `expiry_service._has_successor`; tái dùng, không chép).
  - `probation_expiring_30` «Thử việc hết trong 30 ngày».
  - `overdue` «Đã quá hạn, vẫn đi làm»: SIGNED, `end_date < as_of`, người còn làm, chưa có HĐ nối tiếp (cùng luật nháp của `expiry_service`).
  - `no_contract` «Đang làm, chưa có HĐ»: nhân sự đang làm, chưa từng có HĐ SIGNED / TERMINATED bắt đầu ≤ `as_of`.
  - `missing_scan` «Đã ký, chưa tải bản scan»: đang hiệu lực, `signed_file_id` trống.
  - `second_fixed_term` «Đã ký 2 HĐ có thời hạn»: HĐ đang hiệu lực loại FIXED_TERM và người đó có ≥ 2 HĐ FIXED_TERM đã ký.
  - `new_contracts` «Ký mới trong kỳ»: `start_date` trong kỳ, trạng thái không phải nháp / hủy.
  - `terminated` «Chấm dứt trong kỳ»: `terminated_date` trong kỳ.
- Xem theo: `company` · `department` (cột của HĐ; hàng chưa có HĐ dùng của hồ sơ) · `contract_type`. Breakdown `contract_type`.
- Lọc `department_id` như cột Xem theo phòng ban.
- `/rows`: mọi chỉ số trên. Cột: Mã NV · Họ tên · Phòng ban · Mã HĐ · Loại HĐ · Bắt đầu · Kết thúc · Còn (ngày) · Lương cơ bản · Lương đóng BHXH · Phụ cấp. `link` = `/hr/employees/{id}?tab=labor-contracts`.
- Router mới `labor_contract/report_controller.py`, include TRƯỚC `labor_contract_router` (`/api/labor-contracts/{cid}` nuốt `summary`).

## E1 — `GET /api/employees/profile-gaps/summary` (+ `/export`, `/rows`) · khóa 18 · `require('employee', read|export)`
- Tình trạng HIỆN TẠI (bỏ qua kỳ; `period` vẫn trả để khớp hợp đồng; `totals.compare = null`, `trend = []`).
- Hàng = nhân sự trong phạm vi `apply_scope(Employee, "employee")`; nhân sự đang làm = `status ≠ resigned` và `is_active`.
- Chỉ số (trên nhân sự đang làm):
  - `active_total` «Đang làm» · `complete` (phụ) → dẫn xuất `complete_rate` «Tỷ lệ hồ sơ đủ».
  - `missing_hire_date`, `missing_position` (`position_id = 0`), `missing_manager` (`manager_id = 0`), `missing_department`.
  - Nhóm nhạy cảm — CHỈ khi có `employee_sensitive.read`, thiếu quyền thì bỏ khỏi `meta` + 1 dòng `notes`: `missing_dob`, `missing_id_number`, `missing_tax_code`, `missing_social_insurance`, `missing_bank` (`bank_account_no`), `id_expiring_90` «CCCD hết hạn trong 90 ngày (kể cả đã hết)». Chỉ đếm, không trả giá trị.
  - Nhóm tài khoản — CHỈ khi có `user.read`: `no_account` «Đang làm, chưa có tài khoản đang mở» (tài khoản bị khóa coi như chưa có) · `account_no_role` «Có tài khoản, chưa có vai trò» · `resigned_active_account` «Đã nghỉ, tài khoản còn mở» (hàng nhân sự đã nghỉ có tài khoản `is_active`).
- `complete` = đủ mọi trường đang được đếm cho người xem đó (ghi rõ trong `notes`).
- Xem theo: `company` · `department` (mặc định). Breakdown `gap_kind` (một người thiếu nhiều thứ → nhiều khóa).
- Lọc `department_id` theo `Employee.department_id`.
- `/rows`: mọi chỉ số trừ `complete`. Cột: Mã NV · Họ tên · Công ty · Phòng ban · Chức vụ · Ngày vào làm (+ «Ngày hết hạn CCCD» cho `id_expiring_90`). `link` = `/hr/employees/{id}`.
- Router mới `employee/profile_gaps_report_controller.py`, include TRƯỚC `employee_router`.

## Chung
- Cả 6 đường mới gác `require_report(ReportKey.X)`; `/summary` + `/summary/export` thêm vào `GATED`/`ROUTE_SPECS`; bài riêng cho `/rows` (403 khi không được giao báo cáo).
- Số truy vấn cố định (bài đếm truy vấn với 5 và 50 hồ sơ).
- Mỗi tệp < 200 dòng; tách `*_rows.py` / `*_metrics.py` khi cần.

## Thành công khi
`docker compose exec -T api python -m pytest test/backend -q -k "cr686 or gac_duong"` xanh; thêm `test_pham_vi_luat_bat_bien.py` (bài BB4) vì có controller mới.
