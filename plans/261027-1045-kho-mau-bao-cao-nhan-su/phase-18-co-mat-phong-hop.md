# Phase 18 — C3 Có mặt theo ngày + F1 Sử dụng phòng họp

**Chủ:** BE-8.

## C3 — khóa 26 `ATTENDANCE_DAILY`, `/api/attendance-report` (router khung `work_schedule/attendance_report_controller.py`)
- Gác `require('employee', read|export)` + `require_report(26)` + `apply_scope(Employee)`; số người nghỉ đọc đơn qua `apply_scope(..., 'leave_request')` (thiếu quyền → chỉ số nghỉ trống + ghi chú).
- Mỗi ngày trong kỳ × mỗi người đang làm ngày đó: phải làm hay không (lịch làm việc `work_schedule/resolver_many.load_day_plans_many` + ngày lễ `leave/holiday_calendar`), nghỉ bao nhiêu (đơn đã duyệt phủ ngày đó, nửa buổi = 0,5; dùng lại `leave/report_day_split` hoặc `period_spans`).
- Chỉ số: `scheduled` «Người-ngày phải làm» · `on_leave` «Người-ngày nghỉ (đã duyệt)» · `present` «Người-ngày có mặt» · dẫn xuất `present_rate` «Tỷ lệ có mặt», `absence_rate` «Tỷ lệ vắng» (on_leave / scheduled). Xu hướng theo ngày / tuần / tháng. Xem theo `department` · `company`.
- Trần kỳ: tối đa 92 ngày (người × ngày có thể lớn) → kỳ dài hơn 422 kèm câu rõ ràng. Số truy vấn cố định.
- `/rows`: `on_leave` theo ngày cuối kỳ hoặc theo nhóm: Mã, Họ tên, Phòng, Ngày, Loại nghỉ, Buổi.
## F1 — khóa 28 `ROOM_USAGE`, `/api/room-usage` (router khung `meeting_room/report_controller.py`)
- Gác `require('room_booking', read|export)` (kiểm tên khóa thật trong `core/permissions.py`) + `require_report(28)` + `apply_scope`.
- Lịch đặt đã duyệt (bỏ hủy / từ chối khỏi số giờ, nhưng đếm vào tỷ lệ hủy). Giờ làm việc chuẩn của phòng = giờ làm theo lịch hệ thống (hoặc 8 giờ × ngày làm việc nếu không có).
- Chỉ số: `bookings` «Lượt đặt» · `booked_hours` «Giờ đã đặt» · `available_hours` «Giờ làm việc» · dẫn xuất `occupancy` «Tỷ lệ lấp đầy» · `cancelled` «Đặt rồi hủy / bị từ chối» → `cancel_rate` · `attendees_avg` «Người dự bình quân», `capacity_use` «% sức chứa» (dẫn xuất).
- Xem theo `room` (mặc định) · `company` · `department` (phòng ban đặt) · `hour` «Khung giờ» (8h, 9h…) · `weekday` «Thứ trong tuần». Xu hướng theo ngày / tuần / tháng.
- `/rows`: lượt đặt: Mã, Phòng, Tiêu đề, Người đặt, Phòng ban, Bắt đầu, Kết thúc, Số người, Trạng thái.
- Test cả hai: định nghĩa, phạm vi, trần kỳ, số truy vấn cố định.
