# Phase 04 — Giao diện (frontend-v2)

**Ưu tiên:** cao · **Trạng thái:** pending · **Chủ:** FE · **Phụ thuộc:** hợp đồng ở phase 01

## Chủ tệp
`frontend-v2/src/modules/report/**` · `frontend-v2/src/shared/constants/app-routes.ts` (thêm 2 đường). Không sửa backend.

## Việc
1. **Ô lọc phòng ban dùng chung**: chuyển `components/feature-usage/feature-usage-department-filter.tsx` thành `components/report-department-filter.tsx` (giữ đường import cũ chạy được hoặc sửa chỗ dùng). Gắn làm `extraFilters` cho 5 báo cáo Nhân sự: Biến động, Nghỉ phép, Quỹ phép, HĐLĐ, Hồ sơ thiếu.
2. **Ô lọc trạng thái nhân sự** cho Quỹ phép năm: `employee_status` = Đang làm (mặc định, không ghi URL) · Đã nghỉ · Tất cả. Quỹ phép dùng một `extraFilters` gộp hai ô.
3. **Ngăn «Danh sách người»** (`components/report-drilldown-sheet.tsx` + `api`/`hooks`): `ReportPageConfig.drilldownEndpoint?: string`. Chỉ số có trong `meta.drilldown_metrics`:
   - thẻ KPI có nút nhỏ «Xem danh sách»;
   - mỗi dòng bảng «Xem theo» có nút mở danh sách của nhóm đó (gửi `group_by`, `group_key`; bỏ dòng `__other__`);
   - trong ngăn: chọn chỉ số (trong `drilldown_metrics`), bảng theo `columns` trả về (`kind` → định dạng ngày / số / tiền / ngày nghỉ), dòng có `link` thì bấm mở trang đó, báo «Chỉ hiện 500 dòng đầu» khi `truncated`.
   - Theo `docs/ui/table.md` cho bảng.
4. **Cờ cấu hình trang**: `hideTrend?: boolean` (không vẽ biểu đồ xu hướng — B1, E1) · `hidePeriod?: boolean` (ẩn nút Kỳ báo cáo — E1).
5. **Danh mục + trang mới** (`report-catalog-hr.ts`, `pages/`):
   - «Hợp đồng lao động» — khóa 17, entity `labor_contract`, `/api/labor-contracts/summary`, KPI `active, expiring_30, overdue, no_contract`, `defaultGroupBy: 'department'`, breakdown `contract_type`, `hideTrend`, drilldown `/api/labor-contracts/summary/rows`, `sourcePath` = danh sách nhân sự.
   - «Hồ sơ & tài khoản còn thiếu» — khóa 18, entity `employee`, `/api/employees/profile-gaps/summary`, KPI `active_total, complete_rate, missing_hire_date, resigned_active_account`, `defaultGroupBy: 'department'`, breakdown `gap_kind`, `hideTrend`, `hidePeriod`, drilldown `/api/employees/profile-gaps/summary/rows`.
   - Ba trang cũ thêm `drilldownEndpoint` (`/api/employees/summary/rows`, `/api/leave-requests/summary/rows`, `/api/leave-balances/summary/rows`) và ô lọc. Quỹ phép thêm KPI `people_missing_balance`.
   - Nhãn ở danh mục khớp `REPORT_META` backend (bài kiểm danh mục sẽ soi).
6. Hằng số route: `appRoutes.report.laborContract = '/report/labor-contract'`, `appRoutes.report.hrProfileGaps = '/report/hr-profile-gaps'`.

## Thành công khi
- `docker compose exec -T erp npm run typecheck` và `npm run lint` 0 lỗi.
- `docker compose exec -T erp npx vitest run src/modules/report` xanh, có bài mới cho ngăn danh sách, ô lọc, cờ `hideTrend`/`hidePeriod`.
