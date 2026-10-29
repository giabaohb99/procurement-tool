# duoc-CR-686 · Phase 04 giao diện — báo cáo Nhân sự (giao-dien-v2, 27/10/2026)

## Kết quả
Xong phase 04 trong `frontend-v2/src/modules/report/**` + `shared/constants/app-routes.ts`. Chưa commit (điều phối commit).

## Tệp
Mới:
- `components/report-department-filter.tsx` (chuyển từ `feature-usage/feature-usage-department-filter.tsx`, tệp cũ đã xóa; 3 chỗ dùng đã sửa import: Mức dùng chức năng, Năng lực theo loại việc ×2)
- `components/report-employee-status-filter.tsx`, `components/leave-balance-extra-filters.tsx`
- `components/report-drilldown-sheet.tsx`, `report-drilldown-table.tsx`, `report-drilldown-row-button.tsx`
- `components/report-analytics-body.tsx` (tách thân trang khỏi `report-analytics-page.tsx`, trang cũ đã chạm 199 dòng)
- `api/report-drilldown-api.ts`, `hooks/use-report-drilldown.ts`, `hooks/use-report-drilldown-state.ts`
- `types/report-drilldown.ts`
- `utils/format-drilldown-cell.ts`, `utils/build-drilldown-params.ts`, `utils/report-drilldown-metrics.ts`
- `pages/labor-contract-report-page.tsx`, `pages/hr-profile-gaps-report-page.tsx`
- Bài kiểm: `report-drilldown-sheet.test.tsx`, `leave-balance-extra-filters.test.tsx`, `pages/report-analytics-page-drilldown.test.tsx`, `utils/*drilldown*.test.ts` (3 tệp)

Sửa: `types/report-analytics.ts` (`drilldownEndpoint`, `hideTrend`, `hidePeriod`, `meta.drilldown_metrics?`), `report-kpi-row.tsx`, `kpi-trend-card.tsx` (`action`), `report-grouped-table.tsx` (cột «Danh sách»), `report-filters-bar.tsx` (`hidePeriod`), `report-analytics-page.tsx`, 3 trang HR cũ, `config/report-catalog-hr.ts` (+2 mục khóa 17, 18), `config/report-catalog.test.ts`, `shared/constants/app-routes.ts` (`laborContract`, `hrProfileGaps`).

## Drill-down chạy thế nào
- Nút chỉ hiện khi trang khai `drilldownEndpoint` VÀ chỉ số nằm trong `meta.drilldown_metrics ∩ meta.metrics` (khóa có trong drilldown mà vắng ở metrics bị bỏ).
- Thẻ KPI: link nhỏ «Xem danh sách» (chặn nổi bọt click + keydown để không đổi biểu đồ) → `group_by=none`, không `group_key`.
- Bảng «Xem theo»: cột cuối «Danh sách», nút «Xem» mỗi dòng; dòng Tổng = cả danh sách; dòng `__other__` không có nút; dòng «(Chưa gắn)» gửi `group_key=""`. Chỉ số mặc định: chỉ số biểu đồ → thứ tự `kpis` → chỉ số đầu của backend.
- Tham số = toàn bộ `queryParams` của trang (kỳ, so sánh, công ty, `department_id`, `employee_status`…) + `metric` + nhóm.
- Ngăn (`shared/ui/sheet`): ô chọn chỉ số (chỉ các chỉ số có danh sách), đếm «N dòng», bảng `DataTable` trong `Card` dựng từ `columns` (định dạng theo `kind`: date dd/MM/yyyy, int, days «x ngày», money «x đ»; chấp nhận Decimal dạng chuỗi), thẻ dọc ở màn hẹp (`mobileCard`), dòng có `link` nội bộ bấm mở trang (link ngoài/`//`/`javascript:` bị bỏ), báo «Chỉ hiện N dòng đầu trên tổng M» khi `truncated`, khung xương khi tải, câu lỗi backend + nút «Thử lại», câu rỗng.
- TanStack Query chỉ bật khi ngăn mở; khóa cục bộ `['report','drilldown',endpoint,params]` (không sửa `query-keys.ts` vì ngoài khu được giao — vẫn trúng khi vô hiệu hóa cả `['report']`).

## Cờ
- `hideTrend`: không vẽ biểu đồ xu hướng, thẻ KPI thành tĩnh (không bấm đổi biểu đồ).
- `hidePeriod`: ẩn nút Kỳ báo cáo; lời gọi vẫn gửi kỳ mặc định; bỏ màn «Kỳ này chưa có dữ liệu» (báo cáo tình trạng hiện tại).
- KPI vắng mặt trong `meta` (vd `resigned_active_account` khi thiếu `user.read`): `ReportKpiRow` vốn đã lọc `m != null` — có bài kiểm canh.

## Danh mục
- Khóa 17 «Hợp đồng lao động», entity `labor_contract`, sourcePath = danh sách nhân sự → bài kiểm «khóa quyền khớp mục menu gốc» thêm ngoại lệ `SOURCE_GATE_EXCEPTIONS = {17: 'employee'}` có ghi lý do (HĐLĐ không có màn danh sách riêng).
- Khóa 18 «Hồ sơ & tài khoản còn thiếu», entity `employee`. overviewKpis: HĐLĐ `expiring_30, overdue`; Hồ sơ thiếu `complete_rate`.

## Cổng kiểm
- `npm run typecheck`: 0 lỗi.
- `npm run lint`: 0 lỗi, 30 cảnh báo — không cảnh báo nào nằm trong `src/modules/report` hay `app-routes.ts` (đều ở khu khác, có sẵn).
- `npx vitest run src/modules/report`: 44 tệp / 304 bài xanh. Thêm `src/shared/constants src/app/router`: 3 tệp / 98 bài xanh.
- Trình duyệt (khung riêng, tài khoản mẫu local `admin`): Quỹ phép năm 1440px — ô Phòng ban + Trạng thái nhân sự, thẻ «Chưa được cấp quỹ», nút «Xem danh sách» trên thẻ và từng dòng; ngăn mở đúng 256 dòng quỹ «Phép năm»; 390px — ngăn hiện thẻ dọc. Request thật: `/api/leave-balances/summary/rows?...&group_by=none&metric=people_missing_balance` 200.

## Giả định về backend
- Khóa nhóm «(Chưa gắn)» trong `groups[]` là `""` (đúng `report_compute.bucket_rows`).
- `group_by=none` ở `/rows` = không lọc nhóm (đúng `parse_rows_params`).
- `employee_status` vắng = `working`.
- Hồ sơ thiếu: backend gỡ chỉ số nhạy cảm/tài khoản khỏi cả `metrics` lẫn `drilldown_metrics` khi thiếu quyền.

## Chỗ còn hở
- Chưa xem được hai trang mới trên trình duyệt: admin local chưa được giao khóa 17/18 (`/auth/me` trả 1–16, `/api/labor-contracts/summary` 403 «Chưa được giao xem báo cáo») — chờ migration/`ensure_report_access_defaults` của backend; em không tự ghi DB.
- Lỡ `git mv` một lần làm đổi index chung (đổi tên tệp ô lọc phòng ban); đã `git restore --staged` đúng hai đường đó ngay, index chung về như cũ (không còn gì staged).
- Chưa ghi sổ change-log/nhật ký (điều phối gom khi commit).
