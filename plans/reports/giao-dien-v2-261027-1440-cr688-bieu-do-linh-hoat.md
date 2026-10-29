# duoc-CR-688 · Phase 14 — Biểu đồ linh hoạt (giao-dien-v2)

Ngày 27/10/2026 · nhánh `erp-v2` · CHƯA commit.

## Kết quả
Mọi trang dựng trên `ReportAnalyticsPage` có thẻ «Biểu đồ» mới thay khối xu hướng cũ. Mặc định giống hệt bản cũ (đường xu hướng của chỉ số đang chọn kèm kỳ so sánh, cùng tiêu đề «Xu hướng …»). Người xem đổi được:
- **Vẽ theo**: Thời gian | <chiều «Xem theo» đang chọn>. Không có `trend` (hideTrend / trend rỗng / chỉ số thời điểm) thì ẩn lựa chọn Thời gian, mặc định theo nhóm.
- **Kiểu**: thời gian → Đường / Cột (kỳ này + kỳ so sánh màu xám); nhóm → Cột ngang (mặc định, lớn → nhỏ) / Cột / Vành khuyên (khóa khi > 6 nhóm có số, có số âm, tổng 0 hoặc chỉ số là tỷ lệ).
- **Top N** 5/10/20/Tất cả, phần dư gộp «Khác (n nhóm)», màu xám, không bấm được. Chỉ số `percent`: phần dư bị BỎ chứ không cộng (cộng tỷ lệ là sai), có ghi chú.
- Bỏ nhóm bị che (mọi số `null`), hàng `__other__` của máy chủ, nhóm có số 0; ghi chú nhỏ «N nhóm bị che không vẽ.», «N nhóm bằng 0 không vẽ.», «Phần «Các nhóm khác» máy chủ đã gộp sẵn không vẽ.».
- **Bấm cột / lát** → mở ngăn «Danh sách» của nhóm đó với đúng chỉ số đang vẽ (chỉ khi trang có `drilldownEndpoint` và chỉ số nằm trong `drilldown_metrics`; chặn thêm lúc `meta.group_by` còn lệch «Xem theo» vừa đổi). Vành khuyên có chú giải là nút (đường vào bằng bàn phím).
- **Tải ảnh PNG**: SVG → canvas → PNG, nền đặc, có tiêu đề + kỳ, chú giải vẽ lại ở chân ảnh; tên `bieu-do-<slug>-<từ>-<đến>.png`. Chặn bấm đúp bằng `useRef`, lỗi thì toast.
- URL: `chart_by` / `chart_type` / `chart_top` ghi trong MỘT lượt `setParams`, giá trị trùng mặc định thì xóa khỏi URL; giá trị gõ tay sai thì lùi về mặc định.
- Trang `hideTrend` nay bấm thẻ KPI để đổi chỉ số biểu đồ (trước là thẻ tĩnh).

## Tệp
Mới (của em):
- `frontend-v2/src/modules/report/components/report-flexible-chart.tsx` (+ `.test.tsx`, `-page-drilldown.test.tsx`)
- `.../components/report-flexible-chart-toolbar.tsx`, `-group-bars.tsx`, `-donut.tsx`, `-time-bars.tsx`
- `.../hooks/use-report-flexible-chart-options.ts`, `use-report-flexible-chart-png-download.ts`
- `.../utils/report-flexible-chart-options.ts`, `-series.ts`, `-png.ts`, `-colors.ts` (+ `options.test.ts`, `series.test.ts`)

Sửa:
- `.../components/report-analytics-body.tsx` — thay khe biểu đồ xu hướng; thẻ KPI luôn bấm được; nối bấm nhóm → `drilldown.openRow`.
- `.../hooks/use-report-filters.ts` (+ test) — **ngoài vùng giao, bắt buộc**: `queryParams` chép mọi tham số URL nên `chart_*` lọt vào khóa truy vấn → mỗi lần đổi kiểu biểu đồ gọi lại `/summary`, và rò sang đường xuất Excel / `/summary/rows`. Thêm một điều kiện loại `chart_*`. FE-b chưa đụng tệp này (git sạch lúc sửa).
- `.../pages/report-analytics-page-drilldown.test.tsx` — bài «drops it with hideTrend» khẳng định hành vi cũ (trang hideTrend không có biểu đồ); sửa thành «chuyển sang biểu đồ theo nhóm». Chỉ sửa bài kiểm, không đụng trang.
- `ReportTrendChart` giữ nguyên (trang Tổng quan báo cáo còn dùng).

## Cổng kiểm
- `npm run typecheck`: 0 lỗi.
- `npm run lint`: 0 lỗi, 30 cảnh báo — không cái nào thuộc `src/modules/report` (cảnh báo cũ ở procurement/hr/shared…; CLAUDE.md ghi 23, số trôi do việc khác).
- `npx vitest run src/modules/report`: 55 tệp, 414 bài xanh (bài mới: 56).
- Trình duyệt (Chrome headless qua Playwright — khung chrome-devtools MCP đang bị phiên khác giữ): Báo cáo mua hàng mặc định giống cũ; đổi Cột / Vẽ theo Bộ phận không gọi thêm `/summary`; tải PNG ra `bieu-do-purchase-report-2026-01-01-2026-10-27.png` đúng màu; Hợp đồng lao động mặc định cột ngang theo phòng ban, bấm cột «Hành chính» mở danh sách 2 người (`/summary/rows?...metric=active&group_key=19`, không có `chart_*`); khổ 390px không tràn ngang (scrollWidth 390), thanh điều khiển xuống dòng, nút PNG còn biểu tượng.

## Lượt 2 (theo chốt của điều phối)
Điều phối chốt: (1) giữ màu nhạt cho lát 5–6; (2) giữ màu theo thứ hạng. Làm thêm:
3. **`chart_metric` trên URL** — `pages/report-analytics-page.tsx` bỏ `useState`, dùng `useUrlParamState('chart_metric', config.chartMetric)` (một lượt ghi, trùng mặc định thì xóa). Khóa lạ / chỉ số phụ → lùi về `config.chartMetric` (`resolveChartMetric`, chưa có `meta` thì tạm tin URL). `chart_metric` nằm trong `FLEXIBLE_CHART_URL_PARAMS` nên `useReportFilters` tự loại khỏi tham số gửi máy chủ / Excel / danh sách.
4. **Thẻ KPI chỉ số thời điểm bấm được khi nhóm có số** — `ReportKpiRow` nhận `groupedSnapshotMetrics` (body tính: snapshot nào có số ở ít nhất một nhóm); thẻ đó bấm được, gợi ý «Số dư hiện tại — bấm để vẽ theo nhóm». Biểu đồ: trục thời gian chỉ khi `trend` thật sự mang khóa chỉ số (`trendHasMetric`), nên snapshot luôn vẽ theo nhóm, `chart_by=time` bị bỏ qua. `KpiTrendCard` thêm `aria-pressed` cho thẻ đang chọn.
   - **Đổi hành vi thêm (cần biết):** màn «Kỳ này chưa có dữ liệu» nay KHÔNG hiện khi nhóm còn mang số thời điểm. Lý do: Biến động nhân sự tháng không ai vào/nghỉ trước đây che hết biểu đồ + bảng, nên bấm «Định biên cuối kỳ» không thấy gì. Báo cáo có snapshot chỉ ở Tổng (công nợ mua hàng) không đổi.
5. **Cờ `additive`** — `ReportMetricMeta.additive?: boolean`. `isMetricAdditive`: `false` → không cộng; thiếu cờ → cộng, riêng `percent` luôn không cộng. Không cộng được → bỏ phần dư Top N + ghi chú «Còn N nhóm nhỏ hơn không vẽ (chỉ số này không cộng gộp được).», và khóa vành khuyên.

Tệp thêm lượt 2: `pages/report-analytics-page.tsx`, `types/report-analytics.ts`, `components/report-kpi-row.tsx`, `components/kpi-trend-card.tsx` (+ test: `report-kpi-row.test.tsx`, `report-analytics-page.test.tsx`, `use-report-filters.test.tsx`, các test `report-flexible-chart-*`).

Cổng lượt 2: typecheck 0 lỗi · lint 0 lỗi (30 cảnh báo, không cái nào ở `modules/report`) · `vitest src/modules/report` 55 tệp / 431 bài xanh. Trình duyệt: Biến động nhân sự «Năm nay» bấm «Định biên cuối kỳ» → URL `chart_metric=headcount_end`, không gọi lại `/summary`, vẽ cột ngang theo phòng ban (IDA Global 49 … Khác (8 nhóm) 42).

## Chỗ còn hở / cần quyết
(Mục 1, 2: đã chốt giữ nguyên. Mục 3, 4, 5: đã làm ở lượt 2.)

1. Chỉ có 4 màu phân loại trong `index.css`; vành khuyên lát 5–6 dùng bậc nhạt `color-mix` của màu 1–2. Muốn chuẩn thì khai thêm `--chart-5/6` (sáng + tối) — đụng tệp dùng chung.
2. Màu lát theo thứ hạng (đã xếp lớn → nhỏ), chưa theo thực thể cố định — lọc khác thì màu một nhóm có thể đổi. Có chú giải ghi tên nên không đọc nhầm.
3. Chỉ số đang vẽ (`chartMetric`) vẫn là state của trang, chưa nằm trên URL → link chia sẻ mở đúng kiểu/chiều nhưng về chỉ số mặc định. Muốn đủ thì trang (FE-b) đưa `chart_metric` lên URL.
4. `ReportKpiRow` vẫn chặn bấm thẻ chỉ số thời điểm (vd «Định biên cuối kỳ» ở A1) dù nhóm có số này → chưa vẽ được định biên theo phòng ban trừ khi trang cấu hình nó làm `chartMetric`. Sửa nhỏ ở `report-kpi-row.tsx` nếu đại ca muốn.
5. Gộp «Khác» cộng dồn mọi chỉ số không phải `percent`; chỉ số trung bình kiểu `days`/`hours` (nếu có) sẽ cộng sai. Meta chưa có cờ «cộng được» để phân biệt.
6. Chưa làm theo §3.4 phần mở rộng: tách màu theo chiều thứ hai, cột chồng, bảng nhiệt, tháp tuổi, lưu góc nhìn, ghim Trang chủ, sheet Excel kèm biểu đồ — cần backend `group_by` thứ hai.
7. Chưa ghi dòng sổ (change-log / nhật ký task) vì CR-688 do điều phối giữ — báo lại nếu cần em ghi.

**Status:** DONE_WITH_CONCERNS
**Summary:** Biểu đồ linh hoạt + 3 việc lượt 2 (chart_metric trên URL, thẻ chỉ số thời điểm vẽ theo nhóm, cờ additive) xong; ba cổng xanh, đã soát trình duyệt. Chưa commit.
**Concerns/Blockers:** Đổi hành vi màn «Kỳ này chưa có dữ liệu» khi nhóm còn số thời điểm (mục 4 lượt 2); sửa ngoài vùng giao ở `use-report-filters.ts`; mục 6–7 vẫn mở.
