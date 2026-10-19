# Phase 07 — FE màn admin: danh sách + hồ sơ từng người

**Ưu tiên:** P2 · **Effort:** 9h · **Phụ thuộc:** 05 (cùng PR) · **Trạng thái:** pending

## Ngữ cảnh
- Danh mục báo cáo: `modules/report/config/report-catalog*.ts` là nguồn DUY NHẤT dựng menu + route + thẻ; test
  `report-catalog.test.ts` canh: path dưới `/report`, `sourcePath` khớp mục menu gốc cùng khóa quyền, `key` khớp 1-1 `REPORT_KEY`
  sinh từ backend, nhãn khớp, `reportKeys == [key]`, Tổng quan mang union khóa.
- Gác route: `canAccessRoute` lấy mục menu khớp **tiền tố dài nhất**; không mục nào khớp = MỞ (memory "nav gating fails open").
  ⇒ trang chi tiết PHẢI nằm dưới đường của mục danh sách: `/report/usage-profiles/:userId`.
- `overviewKpis: []` → không góp mặt ở dải KPI Tổng quan (chỉ ở "Danh sách báo cáo").
- Biểu đồ: `shared/ui/chart.tsx`, `column-chart.tsx`, `donut-chart.tsx`, `horizontal-bar-chart.tsx` (recharts); trong module report có
  `kpi-trend-card.tsx`, `report-period-control.tsx`, `report-export-button.tsx`, `report-error-card.tsx`, `report-period-empty-state.tsx` — dùng lại.
- Bảng: `DataTable` (`docs/ui/table.md`), query key ở `shared/constants/query-keys`.

## Danh mục
`modules/report/config/report-catalog-system.ts`:
```ts
{ label: 'Hồ sơ cách làm việc', description: 'Nhịp làm việc, màn hay vào, cách làm phiếu và kiểu làm việc của từng người — chỉ quản trị.',
  path: appRoutes.report.usageProfiles, sourcePath: appRoutes.system.logs, icon: UserSearch,
  key: 14, entity: 'setting', group: 'Quản trị', endpoint: '/api/usage-profiles/summary', overviewKpis: [],
  load: async () => (await import('../pages/usage-profile-list-page')).UsageProfileListPage }
```
`report-catalog.ts` thêm `...SYSTEM_REPORT_CATALOG` (cuối). `routes.tsx` thêm 1 route chi tiết
`appRoutes.report.usageProfileDetail(':userId')` (lazy). `app-routes.ts`: `usageProfiles: '/report/usage-profiles'`,
`usageProfileDetail: (id) => \`/report/usage-profiles/${id}\``.

## Màn danh sách (`pages/usage-profile-list-page.tsx`)
- Bộ lọc: kỳ (`ReportPeriodControl`, mặc định 4 tuần gần nhất) · pháp nhân · phòng ban · vai trò · kiểu làm việc (nhiều lựa chọn, nhãn từ `USAGE_STYLE` sinh) · ô tìm tên/mã.
- `DataTable` phân trang server: Họ tên/Mã · Phòng · Nhóm so sánh · Ngày vào/Ngày làm việc (%) · Lượt ghi · Phiếu lập · Lượt duyệt · Xuất · Lỗi nhập/100 · Kiểu (chip) · Hoạt động gần nhất.
- Nút xuất (`ReportExportButton` → `/summary/export`). Ghi chú đầu trang: "Số liệu có từ ngày {data_since}; sự kiện giao diện từ khi bật thu thập".
- Bấm dòng → `/report/usage-profiles/{user_id}`.

## Màn hồ sơ (`pages/usage-profile-detail-page.tsx`, chỉ ghép khối) — theo bố cục §5 thiết kế
`components/usage-profile/`:
| Tệp | Nội dung |
|---|---|
| `usage-profile-header-card.tsx` | tên · vai trò nhóm · phòng · thâm niên · chọn số tuần (4/8/12) · dòng "đang so với: vai trò X (n người)" hoặc "pháp nhân/toàn công ty vì nhóm < 5" |
| `usage-metric-with-cohort.tsx` | giá trị + "nhóm: trung vị" + mũi tên xu hướng 4 tuần; giá trị `unmeasured` hiện "Chưa đo được — {lý do}", KHÔNG hiện 0 |
| `usage-rhythm-section.tsx` | giờ vào/thao tác cuối (HH:MM), ngày vào/ngày làm việc ròng, phiên làm việc, ngoài giờ, điện thoại · `usage-hour-weekday-heatmap.tsx` (lưới CSS 7×24, đậm theo tỷ lệ — custom vì tầm thường) · dải ngày (đi làm / nghỉ phép / lễ / không vào) |
| `usage-screens-section.tsx` | top 10 màn (`HorizontalBarChart`, nhãn màn từ menu) · % thời gian theo phân hệ (`DonutChart`) · ở lâu nhất · màn mở đầu ngày · 5 đường đi hay gặp · cờ "ước lượng từ API" khi chỉ có nguồn P1 |
| `usage-task-section.tsx` | bảng theo loại phiếu: lập/gửi/duyệt/từ chối/bị trả về · lưu nháp TB · sửa sau gửi · thời gian lập · bỏ form — cột "nhóm" cạnh từng số; duyệt p50/p90, đang chờ |
| `usage-response-section.tsx` | đọc thông báo (tỷ lệ, thời gian), nhắc tên → trả lời, bình luận, trợ lý AI |
| `usage-proficiency-section.tsx` | bộ lọc lưu, 422/100, tìm không ra, hướng dẫn/hỗ trợ, xuất Excel |
| `usage-security-section.tsx` | IP/thiết bị mới, nhiều nơi cùng lúc, xuất vượt mức, xóa hàng loạt, nghỉ việc vẫn hoạt động — rỗng thì "Không có gì bất thường" |
| `usage-style-labels-section.tsx` | chip kiểu + bằng chứng (khóa chỉ số → nhãn) + gợi ý từ `config/usage-style-hints.ts` (chép bảng §4, tầng hiển thị) |
Tiện ích: `utils/usage-route-label.ts` (route mẫu → {phân hệ, màn} dò tiền tố dài nhất trên `allModules[].nav`; không khớp → "Giao diện cũ: {pattern}"),
`utils/usage-format.ts` (phút-trong-ngày → HH:MM, ms → "6 phút 40 giây", tỷ lệ → %).
⚠️ `usage-route-label.ts` import `@/app/router/module-registry` → chỉ import từ component trong trang lazy, KHÔNG từ `config/` hay `routes.tsx` (vòng import registry → report routes).

API/hook/kiểu: `api/usage-profile-api.ts`, `hooks/use-usage-profile-list.ts`, `hooks/use-usage-profile.ts`, `types/usage-profile.ts`; query key thêm ở `shared/constants/query-keys.ts`.

## Tệp
- Tạo: `report-catalog-system.ts`, 2 trang, 10 component, 2 utils, 1 config gợi ý, api/hooks/types + test
- Sửa: `report-catalog.ts`, `report/routes.tsx`, `shared/constants/app-routes.ts`, `shared/constants/query-keys.ts`,
  `modules/system/components/report-access-tab.tsx` (chú thích "13 báo cáo" → không ghi số cứng)

## Todo
- [ ] catalog + route chi tiết + app-routes
- [ ] api/hooks/types
- [ ] màn danh sách + xuất
- [ ] 10 khối hồ sơ + heatmap + utils
- [ ] test gác route, utils, khối rỗng/chưa đo

## Kiểm (vitest)
- `report-catalog.test.ts` xanh với khóa 14 (không sửa luật test, chỉ dữ liệu).
- Gác: `canAccessRoute(reportModule, '/report/usage-profiles/5', canAll, {reportKeys: [1..13]})` → false; có 14 → true; thiếu `setting.read` → false.
- `usage-route-label`: `/procurement/purchase-orders/:id` → phân hệ Thu mua, màn ĐMH (chi tiết); pattern lạ → "Giao diện cũ".
- `usage-format`: 0 → "00:00", 1439 → "23:59", 400000 ms → "6 phút 40 giây", null → "—".
- Khối hồ sơ: chỉ số `unmeasured` hiện "Chưa đo được", không hiện "0"; an toàn rỗng → "Không có gì bất thường"; nhóm < 5 → dòng giải thích fallback.
- Trang danh sách: mock `@/core/api` — lọc nhãn gửi đúng tham số, bấm dòng điều hướng đúng.
Chạy: `docker compose exec -T erp npx vitest run src/modules/report src/modules/system` + `npm run typecheck` + `npm run lint`.

## Rủi ro
| Rủi ro | K × T | Giảm thiểu |
|---|---|---|
| Route chi tiết đặt sai chỗ → mở cho mọi người | Trung bình × Cao | đặt dưới tiền tố mục danh sách + test gác |
| Vòng import module-registry | Trung bình × Trung bình | chỉ import trong trang lazy; typecheck + chạy thử |
| Trang hồ sơ nặng (> 200 dòng) | Cao × Thấp | tách khối như bảng trên |

## Bảo mật
Không có lối vào nào ngoài phân hệ Báo cáo; mục menu ẩn khi thiếu khóa 14 hoặc `setting.read`; backend vẫn là chốt thật.
