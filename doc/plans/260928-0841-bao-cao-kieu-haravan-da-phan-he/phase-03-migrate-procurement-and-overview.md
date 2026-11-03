# Phase 03 — Dời 5 báo cáo Thu mua + trang Tổng quan lên khung mới

## Context links
- Backend: `report/controller.py` (`/procurement` :308, `/pr-lines/summary` :214, `_can_see_ncc` :23), `report/service.py` (`compute_pr_lines_summary` :501, `_pr_lines_base_query`, `order_amount_of`, `received_amount_of`), `purchase_progress/controller.py` (`summarize` :317, `/summary` :384, `_require_progress`), `survey_progress/controller.py` (`summarize` :373, `/summary` :426), `survey/controller.py` (`summarize_report_rows` :375, `/api/survey-report/summary` :415)
- Test cũ phải cập nhật: `test/backend/test_bao_cao_dong_ycmh_tong_hop.py`, `test/backend/test_tong_hop_bieu_do_tien_do_khao_sat.py`
- Frontend: `modules/report/pages/*-chart-page.tsx`, `components/procurement-report-section.tsx`, `pages/report-overview-page.tsx`

## Overview
- Priority: P2 · Status: pending · Effort: 9h
- Các `/summary` Thu mua nhận thêm `date_from/date_to/compare/group_by` và trả hợp đồng chuẩn; giữ `year` (bảng gốc vẫn dùng). Báo cáo mua hàng có đường tổng hợp theo khoảng ngày mới. Tổng quan dựng lại kiểu Haravan cho mọi nhóm.

## Key insights
- Ngày Thu mua là CHUỖI `YYYY-MM-DD` → `range_filter(kind='str')`.
- `/api/reports/procurement` chỉ theo NĂM (`Payable.period == year`) và KHÔNG tự chặn NCC/NSPT (FE gác bằng `purchase_order.read`) → đường mới PHẢI chặn ở backend bằng `_can_see_ncc`.
- Hàm `summarize*` cũ đã đúng luật đếm → giữ, gắn đầu ra vào `breakdowns`; phần `totals/trend/groups` sinh bằng `build_report` trên cùng hàng.
- `purchase-progress` lọc theo NGÀY ĐẶT nhưng bucket theo NGÀY NHẬN → phải chọn một trường ngày (câu hỏi Q3.1).

## Báo cáo (entity = khóa mục menu nguồn — không đổi)
| Báo cáo | Endpoint | Entity | Trường ngày | Chỉ số | Xem theo |
|---|---|---|---|---|---|
| Báo cáo mua hàng | MỚI `GET /api/reports/procurement/summary` | `report` | chi phí: `Payable.incur_date`; đặt hàng: `PurchaseOrder.order_date` | chi phí mua (money), giá trị đặt (money), số ĐMH (int), giao đúng hạn % (good up), công nợ còn lại (snapshot), quá hạn (snapshot, good down) | thời gian · NCC* · NSPT* · bộ phận · nhóm hàng · công ty |
| Chi tiết YC mua hàng | `/api/reports/pr-lines/summary` | `report` | `PurchaseRequest.request_date` | dòng, giá trị, dòng chưa đặt (good down), giá trị chưa đặt, % đã đặt | thời gian · bộ phận · nhóm hàng · NSTM · tiến độ dòng |
| Tiến độ báo giá | `/api/survey-progress/summary` | `survey_request` | `SurveyRequest.request_date` | dòng, đang mở, trễ (good down), đã trả, ngày xử lý TB (good down) | thời gian · NSTM · nhóm hàng · tiến độ |
| Tiến độ mua hàng | `/api/purchase-progress/summary` | `purchase_request` | xem Q3.1 (đề xuất `received_date` cho chỉ số giao, `order_date` cho dòng) | dòng, lần giao, trễ (good down), % đúng hạn, chưa nhận/nhận thiếu/đủ (snapshot) | thời gian · NCC* · bộ phận · tiến độ |
| Báo cáo khảo sát | `/api/survey-report/summary` | `survey` | cột `date` của dòng (đã có `date_from/to`) | dòng KS NCC, KS SP, đã duyệt, % duyệt | thời gian · NSPT · nhóm hàng · kết quả duyệt · loại |
\* NCC/NSPT: chiều chỉ xuất hiện trong `meta.dimensions` khi `_can_see_ncc`/`show_supplier` đúng; `group_by=supplier` khi không có quyền → 403.

Xuất Excel: `.../summary/export` với `require('report','export')`, `_require_progress_export`, `require('survey','export')`, `require('survey_request','export')` (theo đúng luật xuất của bảng nguồn).

## Trang Tổng quan (Haravan)
- Thanh lọc kỳ + so sánh + công ty ở đầu.
- Dải "Chỉ số chính": mỗi báo cáo trong danh mục khai `overviewKpis` (1–2 chỉ số); trang gọi `/summary?group_by=none` CHỈ cho báo cáo người dùng `can(entity,'read')`; nhóm thẻ theo phân hệ.
- Bấm thẻ → biểu đồ xu hướng chính đổi sang chỉ số đó (mặc định thẻ đầu).
- Top lists: 4 khối lấy từ `breakdowns`/`groups` (Top bộ phận chi tiêu, Top NCC* ,Top loại nghỉ, Top dự án quá hạn) — khối nào thiếu quyền thì ẩn.
- Cuối trang: danh sách báo cáo nhóm theo phân hệ (`ReportCatalogList` giữ nguyên).

## Related code files
Sửa (backend): `report/controller.py` (thêm `/procurement/summary` + export, `pr-lines/summary` nhận kỳ — nếu tệp vượt nhiều, tách route mới sang `report/summary_controller.py`), `report/service.py` (tách phần tổng hợp theo kỳ sang tệp mới), `purchase_progress/controller.py`, `survey_progress/controller.py`, `survey/controller.py`; 2 test cũ.
Tạo (backend): `report/procurement_summary_service.py`, `test/backend/test_bao_cao_thu_mua_theo_ky.py`; điền route vào `report/summary_controller.py` (router rỗng P01 đã đăng ký).
Sửa (frontend): `config/report-catalog-procurement.ts` (5 mục + `overviewKpis`), 5 trang `pages/*-chart-page.tsx` → thành cấu hình mỏng dùng `ReportAnalyticsPage`, `pages/report-overview-page.tsx`.
Tạo: `components/report-overview-kpi-strip.tsx`, `components/report-overview-top-lists.tsx`, `hooks/use-report-overview.ts` (`useQueries`).
Xóa: `components/procurement-report-section.tsx`, `components/report-period-filters.tsx`, `components/report-chart-page-header.tsx`, `hooks/use-report-period.ts`, `hooks/use-report-summaries.ts`, `api/report-summary-api.ts`, `types/report-summary.ts`, `utils/pr-lines-chart-data.ts`(+test), hàm tháng trong `utils/report-period-comparison.ts` (giữ `percentChange`, `ratePercent`), `stacked-month-column-chart.tsx` nếu không còn dùng.

## Implementation steps
1. Backend từng endpoint: đọc kỳ bằng `parse_period` CHỈ KHI có `date_from` (thiếu → hành vi `year` cũ, bảng gốc không đổi); `fetch(from,to)` = truy vấn đã scope hiện có + `range_filter`.
2. `procurement_summary_service.py`: dùng `order_amount_of`, `received_amount_of`, `REAL_PO_STATUSES`; chiều NCC/NSPT qua `_can_see_ncc`.
3. Cập nhật 2 test cũ + test mới (kỳ so sánh, NCC bị chặn khi thiếu quyền, `year` cũ vẫn chạy).
4. Frontend: 5 trang thành cấu hình; bỏ `ReportPeriodFilters`; link "Xem bảng chi tiết" mang `year` = năm của `to` (bảng gốc chỉ hiểu năm) + `date_from/date_to`.
5. Tổng quan mới; xóa tệp thừa; 3 cổng kiểm (vitest chỉ `src/modules/report`).

## Todo
- [ ] 4 `/summary` nhận kỳ + export · [ ] `/procurement/summary` mới + export
- [ ] test backend cũ + mới · [ ] 5 trang cấu hình · [ ] Tổng quan · [ ] dọn tệp thừa

## Success criteria
- Số "Chi phí mua hàng" kỳ = Năm nay khớp `/api/reports/procurement?year=` (tính tới hôm nay) trên dữ liệu seed.
- Người thiếu `purchase_order.read`: không có chiều NCC/NSPT, gọi ép `group_by=supplier` → 403.
- Màn bảng gốc Thu mua không đổi hành vi (vẫn `year`).

## Risk assessment
| Rủi ro | K×A | Giảm thiểu |
|---|---|---|
| Lệch số giữa biểu đồ và bảng gốc | TB×Cao | cùng truy vấn gốc; test so khớp tổng |
| Payable theo `period` (năm) ≠ theo `incur_date` | TB×TB | ghi chú `notes`, dùng `incur_date` cho kỳ; Q3.2 |
| `report/controller.py` đã 464 dòng | Cao×Thấp | route mới sang `summary_controller.py` |

## Security considerations
- Chặn NCC/NSPT ở BACKEND (lỗ hiện tại chỉ gác FE). Excel dùng `export`.

## Câu hỏi
- Q3.1 Tiến độ mua hàng: kỳ theo ngày NHẬN (đề xuất) hay ngày ĐẶT?
- Q3.2 Chi phí mua theo `incur_date` (ngày phát sinh công nợ) có đúng ý nghĩa "chi phí trong kỳ"?
