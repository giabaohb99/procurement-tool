# duoc-CR-687 · Phase 09 — giao diện đợt 2 (FE)

## Kết quả
Hai trang báo cáo mới chạy được trên API thật ở :8083 (admin): «Sổ quản lý lao động» (khóa 19) và «Báo cáo sử dụng lao động (01/PLI)» (khóa 20). Nút xuất ghi «Xuất sổ (Excel)» / «Xuất mẫu 01/PLI», tải về đúng tệp xlsx. Nhóm bị che (mọi số null) hiện «—» ở bảng, thẻ KPI, và ở cột Danh sách (không có nút «Xem»). Chưa commit.

## Tệp
- `frontend-v2/src/shared/constants/app-routes.ts` — `report.laborRegister`, `report.laborUsageReport`
- `frontend-v2/src/modules/report/types/report-analytics.ts` — `exportLabel?`, `tableMetrics?` (cột hiện sẵn trên bảng, không lên thẻ)
- `components/report-export-button.tsx` (prop `label`, mặc định «Xuất Excel») · `pages/report-analytics-page.tsx` (truyền `exportLabel`) · `components/report-analytics-body.tsx` (cột bảng = `kpis` + `tableMetrics`)
- `utils/build-report-table-rows.ts` — `isMetricValuesSuppressed`, cờ `isSuppressed` trên dòng · `components/report-grouped-table.tsx` — dòng bị che: «—» thay nút «Xem»
- `config/report-catalog-hr.ts` — 2 mục (19, 20; entity `employee`; `overviewKpis: []`)
- Trang mới: `pages/labor-register-report-page.tsx`, `pages/labor-usage-report-page.tsx`
- Bài kiểm: `pages/labor-register-report-page.test.tsx` (3), `pages/labor-usage-report-page.test.tsx` (4), thêm vào `report-grouped-table.test.tsx` (3), `report-kpi-row.test.tsx` (1), `build-report-table-rows.test.ts` (3); `report-metric-value-cell.test.tsx` bổ sung trường mới cho fixture.
- `statuses.ts` KHÔNG phải của em (backend sinh lại), vẫn đang M trên cây.

## Cổng kiểm
- typecheck: 0 lỗi
- lint: 0 lỗi, 30 cảnh báo, không cái nào nằm trong `src/modules/report` hay `app-routes.ts` (eslint riêng khu này sạch)
- vitest `src/modules/report`: 46 tệp / 318 bài xanh (catalog test 19/20 khớp REPORT_KEY và nhãn backend)

## Kiểm trên API thật
- `/api/labor-register/summary`, `/api/labor-usage-report/summary`: meta/nhãn khớp hợp đồng; `/summary/export` cả hai 200 xlsx (56–72 KB); `/summary/rows` 200 (ngăn danh sách mở được theo phòng ban).
- 1440px: 01/PLI hiện 9 cột chỉ số + Danh sách, cuộn ngang, cột Công ty ghim. 390px (emulate): xem được, thẻ 2 cột.
- Admin đã được gán khóa 19/20 bằng `ensure_report_access_defaults` (chèn 2 dòng).
- Chưa kiểm được trên giao diện việc che nhóm tuổi (admin có `employee_sensitive.read` nên không bị che) — chỉ có bài kiểm đơn vị.

## Quyết định em tự đặt
- Thêm `tableMetrics` (ngoài 2 tinh chỉnh được giao): đề bài muốn job_mid/job_other/ct_* hiện thành cột; khuôn cũ chỉ hiện sẵn cột `kpis`, còn lại phải bật bằng menu «Cột».
- `overviewKpis: []` cho 19/20: backend đòi thêm `employee_sensitive.read` + `labor_contract.read` trong service, người được gán báo cáo mà thiếu quyền sẽ thấy thẻ Tổng quan hỏng; mẫu nộp định kỳ không cần ở dải KPI.
- Nhóm bị che vẫn đi vào khối «rỗng» (mờ, xếp cuối) như dòng toàn 0.

## Chỗ còn hở
- Màn hẹp: mô tả trang ẩn (`max-md:hidden`, khuôn chung) nên câu «Nộp Sở Nội vụ trước 05/6 và 05/12» không hiện trên điện thoại; `notes` backend có câu điền tay nhưng không có hạn nộp. Muốn hiện thì backend thêm một dòng `notes`.
- Màn hẹp: ô lọc Phòng ban / Công ty co còn chữ «T» (có sẵn từ đợt 1, không phải do việc này).
- Tiêu đề cột dài (vd «HĐ khác (thử việc, khoán, CTV, chưa có HĐ)») bị cắt «…» ở 1440 — nhãn do backend đặt.
- Chưa ghi change-log / nhật ký, chưa HDSD (thuộc phần còn lại của phase 09).

**Status:** DONE_WITH_CONCERNS
**Summary:** Đã làm xong 2 trang 19/20 cùng nhãn nút xuất, cột bảng hiện sẵn và cách hiện null cho nhóm bị che; các cổng xanh, đã kiểm trên API thật, chưa commit.
**Concerns/Blockers:** Chưa kiểm được việc che nhóm tuổi trên trình duyệt; trên điện thoại không thấy câu hạn nộp; đã tự thêm `tableMetrics`; để `overviewKpis` rỗng.
