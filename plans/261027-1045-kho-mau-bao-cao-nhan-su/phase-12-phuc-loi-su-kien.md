# Phase 12 — H1 Phúc lợi & sự kiện

**Chủ:** BE-5 · **Khóa:** 22 `BENEFIT_AUDIENCE` · **Đường:** `/api/benefit-audience/summary` (+ `/export`, `/rows`) — router khung `employee/benefit_report_controller.py`.

- Gác: `require('employee', read|export)` + `require_report(22)` + `apply_scope(Employee)`.
- **Ngày dịp** = cuối kỳ đang chọn (`date_to`) — giao diện chọn kỳ «Tùy chọn» một ngày. Người được tính = **đang làm vào ngày dịp** (`hire_date ≤ ngày`, chưa nghỉ hoặc `resign_date > ngày`).
- Tham số lọc (tất cả tùy chọn): `gender` (mã) · `age_min` / `age_max` (tuổi tại ngày dịp) · `birth_month` (1–12) · `seniority_years` (danh sách, vd `1,3,5,10` — tròn năm tại ngày dịp, tính theo tháng của ngày dịp) · `job_level_min` · `position_id` · `exclude_contract_types` (mặc định loại `SERVICE`,`COLLABORATOR`) · `include_on_leave` (mặc định 1; 0 = bỏ người đang có đơn nghỉ đã duyệt phủ ngày dịp) · `child_max_age` (đặt thì đơn vị là **con**: đếm con trai/con gái ≤ tuổi đó tại ngày dịp, từ `tab_employee_family`) · `amount_staff`, `amount_manager` (số tiền; quản lý = cấp bậc ≥ Phó phòng; trống = 0).
- Lọc theo ngày sinh / người thân (`age_*`, `birth_month`, `child_max_age`) đòi `employee_sensitive.read` → thiếu thì 403 câu dễ hiểu.
- Chỉ số: `people` «Số người» · `children` «Số con» (khi có `child_max_age`) · `managers` «Quản lý» · `staff` «Nhân viên» · `budget` «Tổng kinh phí» (money) = Σ (đơn vị × mức tương ứng).
- Xem theo: `company` (mặc định — mỗi pháp nhân hạch toán phần mình) · `department` · `position` · `job_level`. `trend = []`.
- `/rows` metric `people`: Mã NV · Họ tên · Pháp nhân · Phòng ban · Chức vụ · Số con (nếu có) · Mức quà · cột «Ký nhận» trống. KHÔNG in ngày sinh / tên con.
- `/summary/export`: **Danh sách ký nhận** — một sheet mỗi pháp nhân, tiêu đề «DANH SÁCH NHẬN QUÀ <tên dịp>» (tham số `occasion_label`, trần 100 ký tự), STT, cột như `/rows`, dòng Tổng tiền, chỗ ký người lập / duyệt. Chặn công thức (dùng `core/export_xlsx` `_FORMULA_TRIGGER_CHARS`).
- Trần đầu vào: số tiền 0 … 1.000.000.000; tuổi 0 … 120; tháng 1 … 12; sai → 422.
- Test: từng bộ lọc, ngày dịp, người đang nghỉ, đếm con, ngân sách theo hai mức, 403 lọc nhạy cảm, phạm vi, số truy vấn cố định, tệp Excel.
