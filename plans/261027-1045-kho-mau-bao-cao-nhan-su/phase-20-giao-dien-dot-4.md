# Phase 20 — Giao diện đợt 4

**Chủ:** FE-c · `frontend-v2/src/modules/report/**`, `frontend-v2/src/modules/hr/**` (màn kế hoạch + ô Trang chủ), `app-routes.ts`, khai báo khóa quyền phía giao diện cho `headcount_plan` (skill `them-entity-moi` phần frontend + `them-man-v2`).

- Màn **Kế hoạch nhân sự** `/hr/headcount-plans`: khung CRUD khai báo (`shared/crud`), lọc theo năm / pháp nhân / phòng; cột «Quỹ lương kế hoạch / tháng» chỉ hiện khi `can('labor_contract','read')`; nút nhập / xuất CSV như các danh mục khác. Mục menu Nhân sự ▸ Danh mục, gác `headcount_plan`.
- 5 trang báo cáo (danh mục `report-catalog-hr.ts`): «Định biên kế hoạch so với thực tế» (25, `/report/headcount-plan`, preset năm nay, Xem theo pháp nhân, `hideTrend`) · «Có mặt theo ngày» (26, `/report/attendance`, preset tháng này, Xem theo phòng) · «Yêu cầu sửa hồ sơ» (27, `/report/profile-changes`) · «Sử dụng phòng họp» (28, `/report/room-usage`, Xem theo phòng họp) · «Đối tượng cần chú ý theo luật» (29, `/report/legal-watch`, `hideTrend`). Nhãn khớp `REPORT_META`. A5 thêm KPI / cột kế hoạch nếu backend trả.
- Ô **Lịch nhắc trong tháng** ở `hr-dashboard-page.tsx`: ba nhóm (Sinh nhật · Kỷ niệm năm làm việc · HĐ / thử việc hết hạn), chọn tháng, mỗi dòng bấm mở hồ sơ; nhóm nào thiếu quyền thì ẩn.
- Cổng: typecheck (chạy trên máy nếu container erp thiếu bộ nhớ), lint, vitest `src/modules/report` + `src/modules/hr`.
