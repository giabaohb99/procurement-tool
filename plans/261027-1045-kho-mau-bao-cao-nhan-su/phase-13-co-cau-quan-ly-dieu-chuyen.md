# Phase 13 — A3 Cơ cấu quản lý + D1 Điều chuyển & bổ nhiệm

**Chủ:** BE-6 · router khung `employee/management_report_controller.py` (`/api/management-span`, khóa 23) và `employee/work_move_report_controller.py` (`/api/work-moves`, khóa 24).

## A3 — `require('employee', read|export)` + `require_report(23)` + `apply_scope(Employee)`
- Tại mốc `as_of = min(cuối kỳ, hôm nay)`, người đang làm. Hàng = mỗi người (cờ) để gom được theo nhóm.
- Chỉ số: `staff` «Nhân sự đang làm» · `managers` «Người có cấp dưới» (được ai đó trỏ `manager_id`) · `direct_reports` «Tổng cấp dưới trực tiếp» → dẫn xuất `avg_span` «Số cấp dưới bình quân» · `unassigned_manager` «Chưa gán quản lý trực tiếp» · `span_one` «Quản lý chỉ 1 cấp dưới» · `span_wide` «Quản lý trên 10 cấp dưới» · `departures_under` «Nghỉ việc trong kỳ (theo quản lý hiện tại)».
- Xem theo: `department` (mặc định) · `company` · `job_level` · `manager` (mỗi quản lý một dòng — span và số nghỉ dưới quyền).
- `/rows`: `managers` (Mã, Họ tên, Phòng, Chức vụ, Số cấp dưới), `unassigned_manager`, `span_one`, `span_wide`, `departures_under` (người nghỉ + quản lý của họ).
## D1 — `require('employee', read|export)` + `require_report(24)` + phạm vi nhân sự áp lên người của dòng quá trình công tác
- Hàng = dòng `tab_employee_work_history` có `from_date` trong kỳ (đã áp hoặc chưa áp đều tính; ghi chú).
- Chỉ số: đếm theo loại sự kiện `hires`, `transfers`, `appoints`, `concurrents`, `dismisses`, `resigns`, `others` · `people_moved` «Số người có biến động» · `avg_months_to_appoint` «Số tháng từ lúc vào làm tới lần bổ nhiệm» (bình quân trên các dòng bổ nhiệm) · thời điểm: `concurrent_active` «Kiêm nhiệm đang hiệu lực», `concurrent_expiring_30` «Kiêm nhiệm hết trong 30 ngày».
- Xem theo: `event_type` (mặc định) · `department` (phòng đến) · `company` · `flow` «Phòng đi → Phòng đến» (phòng đi = phòng của dòng liền trước cùng người, không có thì phòng hồ sơ trước sự kiện nếu biết, còn lại «(Chưa rõ)»).
- `/rows`: mỗi dòng sự kiện: Mã NV · Họ tên · Loại · Từ ngày · Đến ngày · Phòng đi · Phòng đến · Chức vụ · Số quyết định. KHÔNG trả tệp quyết định.
- Test cả hai: định nghĩa chỉ số, phạm vi, `department_id` chỉ thu hẹp, số truy vấn cố định.
