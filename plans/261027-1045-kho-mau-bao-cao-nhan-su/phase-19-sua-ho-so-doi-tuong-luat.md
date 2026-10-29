# Phase 19 — E2 Yêu cầu sửa hồ sơ + B4 Đối tượng theo luật + dữ liệu ô E3

**Chủ:** BE-9.

## E2 — khóa 27 `PROFILE_CHANGES`, `/api/profile-change-report` (router khung `employee/change_request_report_controller.py`)
- Gác bằng khóa quyền của màn duyệt yêu cầu sửa hồ sơ (đọc `employee/change_request_controller.py` để lấy đúng entity) + `require_report(27)` + phạm vi.
- Chỉ số: `requests` «Số yêu cầu» (theo ngày tạo trong kỳ) · `pending` «Đang chờ» · `pending_over_2d` «Chờ quá 2 ngày» · `approved` · `rejected` → `reject_rate` · `turnaround_hours` (dẫn xuất bình quân giờ xử lý, kind `hours`).
- Xem theo `department` · `company` · `field` «Trường bị xin sửa» (một yêu cầu nhiều trường → nhiều khóa; nhãn trường lấy từ danh mục nhãn hồ sơ) · `status`. Xu hướng theo ngày tạo.
- `/rows`: Mã NV, Họ tên, Phòng, Ngày gửi, Trạng thái, Số trường, Người duyệt, Ngày duyệt — KHÔNG trả giá trị cũ / mới của trường (có thể là CCCD, tài khoản ngân hàng).
## B4 — khóa 29 `LEGAL_WATCH`, `/api/legal-watch`
- Gác `require('employee', read|export)` + `require_report(29)` + `apply_scope` + đòi `employee_sensitive.read` (dùng ngày sinh, con nhỏ) → 403 câu dễ hiểu.
- Tình trạng tại mốc `as_of = min(cuối kỳ, hôm nay)`:
  - `retire_12m` «Đến tuổi nghỉ hưu trong 12 tháng» — tuổi nghỉ hưu theo lộ trình Nghị định 135/2020 (nam 60 tuổi 3 tháng năm 2021, mỗi năm +3 tháng tới 62 năm 2028; nữ 55 tuổi 4 tháng năm 2021, mỗi năm +4 tháng tới 60 năm 2035) — viết hàm thuần có test từng mốc.
  - `maternity_now` «Đang nghỉ thai sản» (đơn đã duyệt loại thai sản phủ `as_of`; nhận diện loại thai sản theo cấu hình loại nghỉ có sẵn — đọc seed / catalog, ghi rõ cách nhận) + ngày đi làm lại.
  - `child_under_12m` «Lao động nữ nuôi con dưới 12 tháng» (từ `tab_employee_family`, quan hệ con).
- Xem theo `department` · `company` · `kind`. `/rows`: Mã, Họ tên, Phòng, Loại, Mốc (ngày đủ tuổi nghỉ hưu / ngày đi làm lại / ngày con đủ 12 tháng) — không in ngày sinh.
## Dữ liệu ô E3 «Lịch nhắc trong tháng» — `GET /api/employees/monthly-reminders?month=YYYY-MM`
- Đặt trong router báo cáo khác hoặc router mới khai TRƯỚC `employee_router`. Gác `require('employee','read')` + phạm vi; sinh nhật (chỉ ngày / tháng) chỉ khi có `employee_sensitive.read`.
- Trả: sinh nhật trong tháng · kỷ niệm 1 / 3 / 5 / 10 năm làm việc trong tháng · HĐ / thử việc hết hạn trong tháng (dùng lại `labor_contract/expiry_service`, cần `labor_contract.read`). Trần 200 dòng mỗi nhóm.
- Test: phạm vi, che sinh nhật khi thiếu quyền, mốc nghỉ hưu, thai sản, con dưới 12 tháng, số truy vấn cố định.
