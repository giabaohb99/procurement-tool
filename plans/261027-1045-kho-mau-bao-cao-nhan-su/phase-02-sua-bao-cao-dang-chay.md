# Phase 02 — Sửa và bù 3 báo cáo đang chạy (A1, C1, C2)

**Ưu tiên:** cao · **Trạng thái:** pending · **Chủ:** BE-1 · **Phụ thuộc:** 01
**Tài liệu:** `doc/erp/hrm/05-bao-cao-nhan-su.md` mục «Ba báo cáo đang chạy», A1, C1, C2

## Chủ tệp (chỉ sửa trong đây)
`backend/app/modules/employee/report_*.py` · `backend/app/modules/leave/report_*.py` · `backend/app/modules/leave/balance_report_*.py` · tệp mới cùng thư mục nếu cần tách (< 200 dòng/tệp) · `test/backend/test_bao_cao_*_cr686.py` (tệp mới của phase này) · sửa bài cũ `test/backend/test_bao_cao_nhan_su.py` nếu hành vi đổi có chủ đích.

## A1 Biến động nhân sự (`/api/employees/summary`)
- Lọc `department_id` theo `Employee.department_id`.
- `notes`: thêm số hồ sơ đang làm THIẾU `hire_date` (đang bị lấy ngày tạo hồ sơ thay). Sửa câu ghi chú «hệ thống chưa lưu lịch sử điều chuyển» thành: phòng ban / chức vụ theo hồ sơ hiện tại; lịch sử điều chuyển đã có ở Quá trình công tác nhưng báo cáo chưa đọc.
- `/summary/rows`: `metric` ∈ `new_hires`, `departures` (sự kiện trong kỳ), `headcount_end` (đang làm tại ngày cuối kỳ). Cột: Mã NV · Họ tên · Công ty · Phòng ban · Chức vụ · Ngày vào làm · Ngày nghỉ việc · Trạng thái. `link` = `/hr/employees/{id}`.
- `meta.drilldown_metrics` như trên.

## C1 Tình hình nghỉ phép (`/api/leave-requests/summary`)
- Lọc `department_id` theo `LeaveRequest.department_id`.
- **Chia ngày theo kỳ.** `days_approved` / `days_pending` (tổng, nhóm, Top loại nghỉ, xu hướng) chỉ tính phần ngày rơi vào kỳ / mốc:
  - Đơn bắt đầu trước kỳ nhưng còn ngày trong kỳ → cộng phần trong kỳ.
  - Đơn bắt đầu trong kỳ nhưng kéo qua cuối kỳ → trừ phần ngoài kỳ.
  - Đơn vắt qua nhiều mốc xu hướng (ngày / tuần / tháng) → chia về đúng mốc.
  - Chia theo từng khoảng (`tab_leave_request_period`, `period_spans.periods_by_request`), trọng số mỗi ngày = số nửa buổi làm việc của ngày đó trong khoảng (lịch làm việc `work_schedule.resolver_many.load_day_plans_many` + ngày lễ `holiday_calendar.holiday_dates` + `workday_service.leave_mask`). Tổng trọng số 0 → chia đều theo ngày lịch. Đơn nhiều loại nghỉ: chia mỗi dòng loại nghỉ theo tỷ lệ `line.days / tổng days`.
  - Chỉ tính lại bằng Python cho đơn VẮT QUA biên (kỳ hoặc mốc); đơn gọn trong một mốc giữ đường SQL hiện có. Số truy vấn cố định (bài kiểm đếm truy vấn như `TestSoTruyVanCoDinh`).
- Số ĐƠN, số người nghỉ, tỷ lệ từ chối, thời gian duyệt: giữ theo ngày bắt đầu (không đổi).
- Chỉ số mới (cột bảng, không KPI): `days_unpaid` «Ngày nghỉ không lương» (dòng đã duyệt của loại `is_paid = False`, cũng chia theo kỳ) · `requests_pending_over_3d` «Đơn chờ duyệt quá 3 ngày» (đang chờ, `submitted_at` cách giờ hiện tại > 72 giờ) · dẫn xuất `avg_days_per_person` = `days_approved / people_on_leave` (kind `days`, `scale=1`).
- `notes`: thay câu «Đơn vắt qua kỳ tính theo NGÀY BẮT ĐẦU» bằng luật mới.
- `/summary/rows`: `metric` ∈ `requests`, `days_approved`, `days_pending`, `requests_pending_over_3d`. Mỗi dòng một đơn: Mã đơn · Mã NV · Họ tên · Phòng ban · Loại nghỉ chính · Từ ngày · Đến ngày · Số ngày trong kỳ · Trạng thái. `link` = `/hr/leave-requests/{id}`.

## C2 Quỹ phép năm (`/api/leave-balances/summary`)
- Tham số mới `employee_status` ∈ `working` (mặc định) | `resigned` | `all` — theo `Employee.status` (`STATUS_RESIGNED`) và `is_active`.
- Lọc `department_id` theo phòng ban HIỆN TẠI của người giữ quỹ.
- Chỉ số mới (cột bảng): `allocated` «Phép năm cơ bản» · `seniority` «Phép thâm niên» · `carried` «Chuyển từ năm trước» · `adjusted` «Điều chỉnh» · `carried_expired` «Phép chuyển đã hết hạn» · `people_over_quota` «Số người vượt quỹ» (còn lại < 0, đếm người) · `people_unused` «Chưa nghỉ ngày nào» (được cấp > 0, đã dùng = 0, giữ chỗ = 0, đếm người).
- Chỉ số thời điểm `people_missing_balance` «Chưa được cấp quỹ» (`snapshot=True`, chỉ ở Tổng): nhân sự đang làm (trong phạm vi + lọc) không có dòng quỹ năm đó cho BẤT KỲ loại nghỉ nào có `counts_balance = True`.
- `/summary/rows`: `metric` ∈ `remaining` (mọi dòng quỹ), `people_over_quota`, `people_unused`, `carried_expired`, `people_missing_balance`. Cột dòng quỹ: Mã NV · Họ tên · Phòng ban · Loại nghỉ · Cơ bản · Thâm niên · Chuyển sang · Điều chỉnh · Đã dùng · Giữ chỗ · Còn lại. Cột chưa cấp quỹ: Mã NV · Họ tên · Công ty · Phòng ban · Ngày vào làm.

## Thành công khi
- Bài kiểm mới: chia ngày (đơn vắt qua tháng, đơn nhiều khoảng, đơn nhiều loại, nửa buổi ở biên, ngày lễ), lọc phòng ban (chỉ thu hẹp, không mở rộng phạm vi), `employee_status`, chưa cấp quỹ, rows của 3 báo cáo (403 thiếu `require_report`, 422 metric lạ, lọc nhóm), số truy vấn cố định.
- `docker compose exec -T api python -m pytest test/backend -q -k "bao_cao_nhan_su or bao_cao_nghi or quy_phep or cr686"` xanh.
