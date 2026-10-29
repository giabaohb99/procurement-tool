# Phase 15 — Giao diện 4 trang mới, kiểm thử, HDSD

**Chủ:** FE-b (giao diện) + điều phối (kiểm thử chéo, rà mã, HDSD, bài canh, commit).

- Danh mục + trang: «Quỹ lương theo pháp nhân» (21, `/report/payroll-fund`, entity `labor_contract`, KPI `payroll_total, people_paid, avg_payroll, insurance_total`, Xem theo `company`, preset `this_month`) · «Phúc lợi & sự kiện» (22, `/report/benefit-audience`, entity `employee`, KPI `people, budget, managers, children`, `hideTrend`, Xem theo `company`) · «Cơ cấu quản lý» (23, `/report/management-span`, KPI `managers, avg_span, unassigned_manager, span_wide`, `hideTrend`) · «Điều chuyển & bổ nhiệm» (24, `/report/work-moves`, KPI `transfers, appoints, people_moved, concurrent_active`, Xem theo `event_type`).
- H1 ô lọc riêng: nút **Dịp có sẵn** (8/3, 20/10 → nữ; 1/6 → con ≤ 14; Trung thu → con ≤ 15; Tết → tất cả; Sinh nhật tháng → tháng của ngày dịp; Kỷ niệm năm làm việc → 1, 3, 5, 10) đặt sẵn bộ lọc; ô Giới tính, Tuổi từ–đến, Mức quà nhân viên, Mức quà quản lý, Tên dịp; công tắc «Tính người đang nghỉ»; chọn **ngày dịp**. Nút xuất «Xuất danh sách ký nhận».
- Điều phối: thêm 12 đường vào bài canh gác quyền + mở khóa cho Trợ lý AI (A5 cố ý ĐÓNG với trợ lý — số lương), rà mã, HDSD, tài liệu 05, sổ, commit.
