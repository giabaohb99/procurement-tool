# Phase 02 — Khung frontend báo cáo (bộ chọn kỳ · trang báo cáo chung · bảng Xem theo)

## Context links
- Hiện trạng: `frontend-v2/src/modules/report/` (catalog, 5 trang, `kpi-trend-card.tsx`, `period-comparison-chart.tsx`, `use-report-period.ts`)
- Dùng lại: `shared/ui/date-range-picker.tsx`, `shared/ui/date-range-presets.ts` (kiểu `DateRangePreset`), `shared/ui/chart.tsx` (`ChartCard`), `shared/ui/horizontal-bar-chart.tsx`, `shared/data-table` (`rowClassName`), `shared/hooks/use-url-param-state.ts`, `use-url-range-param.ts`, `use-single-flight.ts`, `core/api/download-file.ts`
- Luật: `frontend-v2/.claude/rules/*`, `frontend-v2/docs/ui/table.md`
- Hợp đồng JSON: phase-01 mục Architecture

## Overview
- Priority: P1 · Status: pending · Effort: 8h
- Một trang báo cáo CHUNG dựng từ cấu hình + `meta` backend → mỗi báo cáo mới = 1 tệp cấu hình ~30 dòng + 1 dòng danh mục.

## Key insights
- Biểu đồ: recharts 3 (đã có). Không có thư viện xlsx phía FE → xuất Excel ở backend (`downloadFile`).
- `DataTable` không có dòng chân → dòng `Tổng` là hàng giả `id='__total__'` ghim đầu, `rowClassName` in đậm; sắp xếp phía client (dữ liệu nhóm ≤ vài trăm dòng), Tổng luôn đứng đầu. Không sửa `data-table.tsx` (727 dòng, dùng chung).
- Preset "Tháng này / Quý này / Năm nay" của báo cáo phải chạy TỚI HÔM NAY (khác preset màn danh sách, tới cuối kỳ) — nếu không "so kỳ trước" luôn giảm (đúng lỗi mà `comparableMonthCount` đang vá tay).
- URL lưu `preset` (không chỉ ngày) → link "Tháng này" gửi cho nhau vẫn là tháng này khi mở; `preset=custom` mới dùng `from/to`.
- Test danh mục (`report-catalog.test.ts`) đòi `src.entity === r.entity`; mục menu Văn bản CỐ Ý không khai entity → nới luật: thiếu entity ở mục menu thì so với entity của PHÂN HỆ (báo cáo chỉ được CHẶT hơn nguồn).

## Requirements
- Preset (10): Hôm nay · Hôm qua · 7 ngày qua · 30 ngày qua · Tháng này · Tháng trước · Quý này · Năm nay · Năm trước · Tùy chọn khoảng ngày. Mặc định: 30 ngày qua (xem câu hỏi).
- So sánh với: Kỳ trước (mặc định) · Cùng kỳ năm trước · Không so sánh.
- URL: `preset`, `from`, `to`, `compare`, `group_by`, `company_id` + lọc riêng. Tương thích link cũ `?year=2025` → `preset=custom&from=2025-01-01&to=2025-12-31`.
- Trang chi tiết: Header (tiêu đề · "Xem bảng chi tiết" nếu có `sourcePath` bảng · Xuất Excel nếu `can(entity,'export')`) → thanh lọc → hàng KPI (giá trị, ±% so sánh có mũi tên + màu theo `good`, sparkline từ `trend`) → biểu đồ xu hướng (chọn chỉ số bằng bấm thẻ KPI) → breakdowns tùy chọn → bảng nhóm có "Xem theo", Tổng, cột kỳ so sánh + ±% (ẩn khi `compare=none`).
- Nhãn trục/khóa đọc từ `label` backend; định dạng số theo `kind` (int · money dùng `shortMoney`/`formatMoney` · days 1 số lẻ · hours → "x giờ"/"y ngày" · percent).
- Chặn bấm đúp Xuất Excel bằng `useSingleFlight` (bẫy `disabled` của CLAUDE.md).

## Architecture
```
ReportAnalyticsPage(config)
 ├─ ReportPageHeader(title, sourcePath, ReportExportButton)
 ├─ ReportFiltersBar(ReportPeriodPicker, ReportCompareSelect, company, config.extraFilters)
 ├─ ReportKpiRow(meta, totals, trend) → KpiTrendCard × n  (onSelect → chartMetric)
 ├─ ReportTrendChart(trend, metric) → PeriodComparisonChart (tổng quát hóa kiểu điểm)
 ├─ ReportBreakdownCharts(breakdowns, config.breakdowns) → HorizontalBarChart
 └─ ReportGroupedTable(meta, totals, groups, compare) + ReportGroupBySelect("Xem theo")
useReportFilters() ⇄ URL ; useReportAnalytics(endpoint, params) → TanStack Query (keepPreviousData)
```
Cấu hình: `ReportPageConfig { endpoint, exportEndpoint, entity, title, description, sourcePath?, kpis: string[], chartMetric, defaultGroupBy, breakdowns?: {key,title}[], extraFilters?: ComponentType, hideCompany? }`.

## Related code files
Tạo (`frontend-v2/src/modules/report/`):
- `config/report-period-presets.ts` (+`.test.ts`) — 10 preset dựa `DateRangePreset` + `key`
- `hooks/use-report-filters.ts` (+`.test.tsx`) — URL state, map `year` cũ
- `types/report-analytics.ts` — kiểu hợp đồng + `ReportPageConfig`
- `api/report-analytics-api.ts` — `get(endpoint, params)`, `export(endpoint, params, filename)`
- `hooks/use-report-analytics.ts`
- `utils/format-report-metric.ts` (+test) — theo `kind`
- `utils/build-report-table-rows.ts` (+test) — dòng Tổng + nhóm + ±%, sắp client
- `components/report-period-picker.tsx` — Select preset + `DateRangePicker showPresets={false}` khi "Tùy chọn"
- `components/report-compare-select.tsx`, `components/report-group-by-select.tsx`
- `components/report-filters-bar.tsx` (thay `report-period-filters.tsx`)
- `components/report-page-header.tsx` (thay `report-chart-page-header.tsx`)
- `components/report-export-button.tsx`, `components/report-kpi-row.tsx`, `components/report-trend-chart.tsx`, `components/report-breakdown-charts.tsx`, `components/report-grouped-table.tsx`
- `pages/report-analytics-page.tsx` (<200 dòng)
- Danh mục tách nhóm: `config/report-catalog-hr.ts`, `config/report-catalog-admin.ts`, `config/report-catalog-work.ts` (mảng rỗng — P04/05/06 sở hữu); `config/report-catalog-procurement.ts` (chuyển 5 mục hiện có sang, P03 sở hữu)
Sửa:
- `config/report-catalog.ts` — ghép 4 mảng nhóm; thêm `sourceIsTable?: boolean` (ẩn nút "Xem bảng chi tiết" khi nguồn không phải bảng)
- `config/report-catalog.test.ts` — luật entity dự phòng theo phân hệ
- `components/period-comparison-chart.tsx` — kiểu điểm tổng quát `{label, current, previous}` (bỏ phụ thuộc `MonthComparisonPoint`)
- `shared/constants/app-routes.ts` — thêm TRƯỚC mọi đường mới của P04–P06: `/report/hr-headcount`, `/report/leave-usage`, `/report/leave-balance`, `/report/vehicle-booking`, `/report/seal-request`, `/report/document`, `/report/approval`, `/report/work`
- `shared/constants/query-keys.ts` — `report.analytics(endpoint, params)`

## Implementation steps
1. Preset + test với `today` cố định (đầu năm, đầu tháng, quý, năm nhuận; Hôm qua qua ngày 1).
2. `use-report-filters` (một lần `setSearchParams` cho nhiều tham số, `replace: true`, như `useUrlRangeParam`); đổi `group_by` KHÔNG đổi kỳ.
3. Kiểu + API + hook; query key gồm endpoint + mọi tham số.
4. Thành phần UI (mỗi tệp <200 dòng); `ReportGroupedTable` dùng `DataTable` với `storageKey="report.<slug>"`, cột dựng `useMemo` từ `meta`.
5. `ReportAnalyticsPage` + trang mẫu tạm trong test (render với API giả qua MSW/vi.mock theo `testing.md`).
6. Tách danh mục theo nhóm, nới test, thêm hằng route.
7. `npm run typecheck` · `npm run lint` · `npx vitest run src/modules/report`.

## Todo
- [ ] presets + test · [ ] use-report-filters + test · [ ] types/api/hook
- [ ] 10 thành phần UI · [ ] report-analytics-page · [ ] tách danh mục + nới test
- [ ] app-routes + query-keys · [ ] 3 cổng kiểm xanh

## Success criteria
- Đổi preset/so sánh/Xem theo → URL đổi, F5 giữ nguyên; link `?year=` cũ vẫn mở đúng kỳ.
- Test: preset đúng 10 khoảng; dòng Tổng luôn đầu kể cả khi sắp; cột so sánh ẩn khi `compare=none`; ±% `null` khi kỳ so sánh = 0 hiện "—".
- typecheck + lint 0 lỗi; vitest `src/modules/report` xanh.

## Risk assessment
| Rủi ro | K×A | Giảm thiểu |
|---|---|---|
| `defaultHidden`/bố cục cũ trong localStorage che cột mới | TB×Thấp | `storageKey` mới `report.<slug>.v2` |
| Nới test danh mục làm lỏng quyền | Thấp×Cao | chỉ nới khi mục menu KHÔNG có entity, và phải bằng entity phân hệ; thêm case test |
| Trang chung phình >200 dòng | TB×Thấp | tách khối thành component như trên |

## Security considerations
- `can()` chỉ để ẩn nút; quyền thật ở backend. Nút Excel ẩn khi thiếu `export`.

## Next steps
P03–P06 chỉ viết cấu hình + endpoint.
