# Phase 04 — FE: trang báo cáo ngày lễ + Tổng hợp theo người + hộp Cấp quỹ có lọc

## Context
- API phase 03. Mẫu: `report/pages/attendance-report-page.tsx` (`ReportAnalyticsPage` + `ReportPageConfig`),
  `report/config/report-catalog-hr.ts` (+ `.test.ts` danh sách khóa), `report/pages/leave-balance-report-page.tsx`,
  `hr/pages/leave-balance-page.tsx` (421 dòng — logic mới vào component riêng), `backend/scripts/gen_status_ts.py`.
- Chạy sau phase 02 (chung `shared/constants/app-routes.ts`) và phase 03 (API).

## Việc
1. Chạy `python backend/scripts/gen_status_ts.py` (trong `api` hoặc host) → `shared/constants/statuses.ts` có khóa 30 + nhãn.
2. `report-catalog-hr.ts` thêm mục: `label: 'Làm việc vào ngày lễ, ngày nghỉ'` (khớp `REPORT_META`), `key: 30`, `entity:
   'leave_comp_request'`, `group: 'Nhân sự'`, `endpoint: '/api/holiday-work-report/summary'`, `sourcePath:
   appRoutes.hr.leaveCompRequests`, icon `CalendarCheck` (lucide), `overviewKpis: ['lines']`, `load` trang mới. Cập nhật
   `report-catalog-hr.test.ts`.
3. `report/pages/holiday-work-report-page.tsx`: `kpis: ['lines','people','holiday_lines','comp_days']`, `tableMetrics:
   ['offday_lines']`, `chartMetric: 'lines'`, `defaultGroupBy: 'department'`, `defaultPreset: 'this_year'`,
   `drilldownEndpoint`, `extraFilters`: phòng ban (dùng `ReportDepartmentFilter`) + component nhỏ
   `holiday-work-report-filters.tsx` (ô **Loại ngày** + ô tick **Gồm phiếu chờ duyệt** → query `day_kind`, `include_pending`).
   Mô tả nói rõ **Không có chấm công — chỉ người đã lập phiếu nghỉ bù**.
4. `shared/constants/app-routes.ts`: `report.holidayWork: '/report/holiday-work'`.
5. `report/pages/leave-balance-report-page.tsx`: thêm `comp` vào `tableMetrics`.
6. **Tổng hợp theo người** trên màn Quỹ phép: hai thẻ **Theo dòng quỹ | Theo nhân sự** ở đầu `leave-balance-page.tsx`
   (nhớ ở URL `?view=people`); thẻ mới = `components/leave-balance-matrix-table.tsx` (`DataTable`, cột động theo `columns`,
   số âm tô đỏ, cột Tổng, nút *Xuất Excel* gác `can('leave_balance','export')`); API/hook ở tệp mới
   `api/leave-balance-matrix-api.ts` + `hooks/use-leave-balance-matrix.ts`.
7. **Hộp Cấp quỹ** `components/leave-balance-allocate-dialog.tsx` thay nút bấm-là-chạy: năm (khóa theo năm đang xem) ·
   loại nghỉ (chọn nhiều, trống = mọi loại trừ quỹ) · pháp nhân · phòng ban · hình thức NV · cấp bậc → gọi allocate cũ với
   ô mới; kết quả giữ câu **thêm N dòng** + danh sách thiếu ngày vào làm như hiện tại. Hook allocate: thêm tham số ở tệp hook
   mới (không sửa `leave-api.ts` của CR-715 nếu tránh được; nếu phải sửa thì chỉ thêm trường kiểu).

## Tệp
Tạo: `report/pages/holiday-work-report-page.tsx` · `report/components/holiday-work-report-filters.tsx` (+ test) ·
`hr/components/leave-balance-matrix-table.tsx` (+ test) · `hr/components/leave-balance-allocate-dialog.tsx` (+ test) ·
`hr/api/leave-balance-matrix-api.ts` · `hr/hooks/use-leave-balance-matrix.ts`.
Sửa: `shared/constants/statuses.ts` (sinh tự động) · `shared/constants/app-routes.ts` · `report/config/report-catalog-hr.ts`
(+ test) · `report/pages/leave-balance-report-page.tsx` · `hr/pages/leave-balance-page.tsx` (chỉ gắn thẻ + hộp).
KHÔNG đụng: tệp của phase 02.

## Bài kiểm
- `report-catalog-hr.test.ts`: khóa 30 khớp đường + endpoint + entity; test chung khớp nhãn với `REPORT_KEY` sinh tự động.
- `holiday-work-report-filters`: đổi ô → query đúng tên tham số.
- `leave-balance-matrix-table`: cột động theo dữ liệu, ô trống hiện **—**, số âm có lớp đỏ, nút xuất ẩn khi thiếu quyền.
- `leave-balance-allocate-dialog`: gửi đúng `leave_type_ids` + bộ lọc; ô trống không gửi (hoặc gửi 0).
- Cổng: typecheck (host) 0 lỗi · `npx eslint src/modules/hr src/modules/report` 0 lỗi · `npx vitest run src/modules/report`
  + `src/modules/hr` xanh.

## Xong khi
Trên `localhost:8083`: admin (đăng nhập lại để nhận `report_keys`) thấy thẻ báo cáo mới ở phân hệ Báo cáo, lập phiếu nghỉ
bù ngày lễ → duyệt → báo cáo ra 1 lượt đúng tên lễ; màn Quỹ phép thẻ **Theo nhân sự** ra ma trận và xuất Excel; hộp Cấp quỹ
lọc theo phòng chỉ tạo dòng cho phòng đó.

## Rủi ro
| Rủi ro | K×T | Giảm |
|---|---|---|
| Quên chạy `gen_status_ts.py` → nhãn khóa 30 thiếu, test đỏ | TB × Thấp | bước 1 bắt buộc |
| `leave-balance-page.tsx` phình thêm | Cao × Thấp | logic vào component; trang chỉ thêm thẻ + mở hộp |
| Người cũ chưa đăng nhập lại không thấy báo cáo | Cao × Thấp | ghi vào HDSD + câu trả lời hỗ trợ |
