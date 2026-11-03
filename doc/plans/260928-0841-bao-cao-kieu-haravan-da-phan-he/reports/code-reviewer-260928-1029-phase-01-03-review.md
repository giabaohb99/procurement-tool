# Code review — P01–P03 báo cáo kiểu Haravan (uncommitted, erp-v2)

## Scope
- Backend: core/report_period.py, report_aggregate.py, report_export.py, export_xlsx.py, main.py; report/{summary_controller, procurement_summary_service, procurement_summary_rows, pr_lines_period_service, controller}.py; purchase_progress/{controller, summary_service}.py; survey_progress/{controller, summary_service}.py; survey/{controller, report_summary_service}.py
- Frontend: frontend-v2/src/modules/report/**, shared/constants/query-keys.ts
- Tests run: 5 backend files -> 68 passed; `vitest src/modules/report` -> 67 passed. typecheck/lint NOT run (resource rule).

## Overall
Auth wiring is correct. Every new `/summary` and `/summary/export` route reuses the source table's guard and scope. Export routes require the `export` action. No route is shadowed by a `/{id}` route. NCC/NSPT gating is enforced in the backend for the new routes. Dual mode (`preset` present or absent) is preserved. The remaining problems are correctness and semantics issues in the shared framework, which will spread to P04–P06 if not fixed now.

## Verified OK (checklist)
- Guards: procurement summary uses `require(report,read|export)` (summary_controller.py:24,35); pr-lines uses `report read|export` (report/controller.py:219,241) with scope via `_pr_lines_base_query` → `report_dept_scope`; purchase-progress uses `_require_progress` / `_require_progress_export` with the same `_build_query` (apply_scope PO or PR-link); survey-progress uses `survey_request read|export` with `_build_query` (apply_scope + `_line_visible_cond`, controller.py:297-298); survey-report uses `survey read|export` with `apply_scope(Survey)`.
- Shadowing: no `/{id}` route exists on /api/reports, /api/purchase-progress, /api/survey-progress or /api/survey-report. `report_summary_router` is included before `report_router` (main.py:277).
- NCC: `supplier`/`nspt` are left out of both dimensions and breakdowns when `_can_see_ncc` is false (procurement_summary_service.py:62-70), and `group_by` is forced to 403 (:80). Purchase-progress gates on `supplier.read` (summary_service.py:86; controller 403). No supplier name reaches labels, notes or the Excel file without the permission. `company_id` is only ever ANDed after scope, so it cannot widen it. `report` is PUBLIC in SCOPE_FIELDS.
- Period math: calendar presets shift with end-of-month clamp; rolling presets use the same length before; `year` handles 29/02→28/02; cap is 1096 days; malformed input returns 422 in the envelope. `range_filter` datetime_utc subtracts VN_OFFSET.
- DerivedSpec scale: every percent derived uses ×100 correctly; `avg_handling_days` uses scale=1. No other average is inflated.
- FE: `?year=` maps to custom; double-click on export is blocked by `useSingleFlight`; export button is gated by `can(entity,'export')`; overview `useQueries` only runs for `can(entity,'read')`; no hand-written status lists; money formatted with `formatMoney`; table uses `DataTable`.

## Critical
None.

## High

### H1. Trend comparison misaligned: compare period bucketed with its OWN granularity, and weeks paired by index
report_aggregate.py:196-198 calls `resolve_granularity(compare_from, compare_to)`, and `_merge_by_index` (:171) pairs bucket i of the current period with bucket i of the compare period.
- Reproduced: `this_quarter` on 2026-08-01 gives current 07-01..08-01 (32 days → **week**, 5 buckets) against compare 04-01..05-01 (31 days → **day**, 31 buckets). Week bucket i is compared with day i, so the numbers are silently wrong. The same happens with custom 32-day ranges that span 29/02 when `compare=year`.
- Even when both sides are weekly, partial first weeks differ in size, because each axis starts on its own Monday. Example: `last_30_days`-style rolling ranges of 32–92 days, or `compare=year` (weekday shifts). A 1-day compare week then sits against a 7-day current week and the ±% is skewed.
- Fix: bucket the compare rows onto the CURRENT axis by day offset: `d_shifted = d + (period.date_from - period.compare_from)`, then `bucket_of(d_shifted, period.granularity)`, and drop rows past `date_to`. At minimum, pass `period.granularity` for the compare period. Day-level index alignment (this_month vs last month, day i ↔ day i) is fine as is.

### H2. Derived rate with denominator 0 returns 0, not "no data"
report_aggregate.py:104 has `... if den else 0`.
- Scenario: "Hôm nay", or any day/week with no deliveries, gives `on_time_rate = 0`. The KPI then shows 0% and "−100% so với kỳ trước" in red (report-kpi-row.tsx:66). The daily trend line dives to 0% on every day without deliveries. The Excel file shows 0.0%.
- Fix: return `None` when `den == 0`. The FE already renders null as "—" (format-report-metric.ts), and `percentChange` needs a null guard (`current ?? null`). In report_export, keep `cell_value` percent None → leave empty rather than 0.

## Medium

### M1. Snapshot metrics shown as 0 in groups, trend and Excel
`debt_remaining` / `debt_overdue` are declared as MetricSpec with `value_of=0` (procurement_summary_service.py:47-48), and only `totals` get overwritten (report_aggregate.py:199-202).
- In the "Xem theo" table every department/company row shows 0 debt while the Tổng row shows the real number. The `debt_overdue` KPI sparkline is flat 0, and clicking it draws an all-zero chart. Excel group rows also show 0.
- Fix: flag these metrics as `snapshot=True` in meta. The FE then excludes them from table, trend and chart selection, and `report_xlsx` writes them only on the Tổng row. Alternatively, add them to `hiddenMetrics` and make them non-selectable.

### M2. pr-lines: the note claims "Tiến độ dòng vẫn đếm đủ, kể cả dòng hủy" — it doesn't
pr_lines_period_service.py:25-33 and :81.
- Every metric zeroes out cancelled lines. As a result, the `cancelled` group in `group_by=line_status` shows 0 lines, and the breakdown (ranked by `amount`, zeros dropped) removes it entirely. The cancel-rate view of the old summary is lost, and the note shown to users is false.
- Fix: add an uncounted metric such as `all_lines` (includes cancelled) and use it as `rank_by`/column for the line_status dimension, or drop the note.

### M3. Plan deviation Q3.1 (purchase-progress delivery metrics dated by order_date)
The decision recorded in plan.md:62 is: delivery metrics by `received_date`, line count by `order_date`. The implementation uses `order_date` for everything (purchase_progress/summary_service.py:5-6, controller fetch).
- The note shown to users also says "xem Q3.1", which is an internal planning reference (summary_service.py:17-18).
- Needs an explicit sign-off, or an implementation using `received_date` for delivery rows.

### M4. Procurement summary ignores `report_dept_scope`
`/api/reports/matrix` limits department rows for requester departments (report scope `dept`) via `report_dept_scope` (controller.py:115-117), and pr-lines does the same (service.py:476). The new `/procurement/summary` exposes spend and order value for ALL departments (dimension + breakdown) and company totals.
- It is no looser than legacy `/procurement`, which is also unscoped, but it is looser than `/matrix`.
- Decide: apply `allow` to PO rows (department IN allow) when not None, or confirm that "báo cáo mua hàng = toàn công ty" is intended.

### M5. Excel formula injection via group labels
`xlsx_response` writes str cells as-is (export_xlsx.py:153), and openpyxl turns any string starting with `=` into a formula (verified: `data_type == 'f'`).
- New surface: supplier names, departments, item groups and NSPT labels in `report_xlsx` groups, all user-entered.
- Fix (shared helper, benefits all exports): in `cell_value` for kind text, when `s[:1] in "=+-@"`, prefix `'` or set `c.data_type = 's'` after assignment.

### M6. FE dead-end on 403/422
A URL with `group_by` that the user can't use (shared link with `group_by=supplier` to a user without `purchase_order.read`, or a typo) returns 403/422. After that, `meta` falls back to `dimensions: []` (report-analytics-page.tsx:59), so the "Xem theo" select has no options, the KPIs are empty, and the only fix is editing the URL by hand.
- Fix: on error with a non-default `group_by`, reset it (`setGroupBy(config.defaultGroupBy)`), or keep the last good meta / a static dimension list from config.

## Low
- L1. Compare-only groups disappear: `_merge_by_key` iterates only current groups (report_aggregate.py:180-182). A supplier or department with 100M last period and 0 now is invisible, so declines are hidden. Consider a union of keys with current = zeros.
- L2. Extreme dates → 500: custom `0001-01-01` → OverflowError; with `compare=year` → ValueError year 0; `9999-12-31` → `range_filter` upper overflow. Add a year range check (e.g. 2000–2100) in `_parse_date_param` → 422 (CLAUDE.md "dải năm hợp lý").
- L3. `company_id=abc` → `int()` ValueError → 500 in procurement_summary_rows.py:61,95,113 and `_pr_lines_base_query`. Validate with `isdigit` like purchase-progress does.
- L4. Helper metrics (`deliveries_done`, `handling_days_sum/count`) are hidden only on the FE (`hiddenMetrics`), but still appear as columns in the Excel export and in `meta`. Better: an `internal=True` flag on MetricSpec that `_meta` and `report_xlsx` skip.
- L5. The Excel `±%` of percent-kind metrics is a relative change of a rate (80%→40% = −50%), not percentage points. The same applies in the FE KPI. Decide which one, and label it.
- L6. Overview: `ReportOverviewTopLists` renders "Top bộ phận / Top nhóm hàng" empty cards ("Kỳ này chưa có dữ liệu.") when the user lacks `report.read` but has another report (report-overview-page.tsx:84-87). Plan says to hide it. Guard with `procurementEntry &&`.
- L7. Overview sends `company_id` to survey-report, which ignores it (that page sets `hideCompany`), so the KPI strip mixes filtered and unfiltered numbers without saying so.
- L8. Survey-report period mode still loads EVERY in-scope survey line (`service.report_rows`) regardless of period, even for "Hôm nay". This is pre-existing in `/lines`; consider pre-filtering surveys by `received_date` range with a margin.
- L9. Dead query keys `prLinesSummary / purchaseProgressSummary / surveyProgressSummary / surveyReportSummary` (query-keys.ts:660-667) are no longer used anywhere.
- L10. The main.py:277 comment says "xem ghi chú ở import", but no such note exists at the import line.
- L11. Survey-progress `open_lines` / `late` are "as of today" states, so for the compare period they mean "lines from last period still open/late now". This is semantically odd; consider adding a note.

## Pre-existing (not introduced, still open)
- Legacy `GET /api/reports/procurement` still returns `by_supplier` / `by_nspt` to anyone with `report.read` (controller.py:480-484). The new route fixes this only for the new UI; v1 and the Thu mua table still hit the old one.

## Recommended order
1. H1 (bucket compare on the current axis by day offset) and H2 (null on den=0), in the framework before P04–P06 copy it.
2. M1, M2, M5, M6.
3. Decide M3 and M4 with the owner (đại ca).
4. Lows opportunistically; L2 and L3 are one-liners.

## Unresolved questions
- Q3.1: keep `order_date` for delivery metrics (current code) or switch to `received_date` (plan decision)?
- Should procurement summary respect `report_dept_scope` (M4)?
- ±% for rate metrics: relative % or percentage points?
