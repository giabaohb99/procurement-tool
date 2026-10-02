# Phase 05 — FE: gác menu/route/Tổng quan theo `report_keys`

Plan: `frontend-v2/plans/261002-0836-phan-quyen-tung-bao-cao/phase-05-frontend-report-gating.md`.
Không commit.

## Thiết kế đã làm
- `AuthUser.report_keys?: number[]` (`src/core/auth/auth-types.ts`) — khớp hợp đồng `/auth/me`
  của phase 02 (mảng int sorted, rỗng = chưa gán).
- `useNavContext()` (`src/core/authorization/use-permission.ts`) trả thêm `reportKeys` — đọc
  THẲNG `s.user?.report_keys` (không `?? []`) để giữ tham chiếu ổn định, tránh `useQueries`/
  `useMemo` ở nơi dùng nghĩ dữ liệu vừa đổi mỗi lượt render.
- `NavContext.reportKeys` (`module-visibility.ts`) + `ModuleNavItem.reportKeys`
  (`module-definition.ts`). Gác trong `itemAllowed`: SAU `if (!baseOk) return false`, thêm
  `if (item.reportKeys && !item.reportKeys.some((k) => ctx.reportKeys?.includes(k))) return false`
  — ngược chiều mặc định "không khai entity = luôn hiện": mục CÓ khai `reportKeys` mà ctx
  thiếu/rỗng/không khớp thì luôn ẨN (fail-closed).
- `ReportCatalogEntry.key: number` (`config/report-catalog.ts`) — gắn đúng `ReportKey` backend
  (1..13) vào 13 mục ở 5 tệp nhóm (`report-catalog-{procurement,hr,admin,document,work}.ts`),
  thứ tự đúng khớp contract phase 01-03: PURCHASE_REPORT=1 … WORK=13. Mỗi literal có comment
  `// ReportKey.<TÊN> (backend) = N`.
- `routes.tsx`: mục Tổng quan mang `reportKeys: REPORT_CATALOG.map((r) => r.key)` (union, giữ
  `entities` cũ); mỗi mục báo cáo mang `reportKeys: [r.key]`.
- `utils/filter-visible-reports.ts` (mới) — `filterVisibleReports(reports, can, reportKeys)` =
  `can(entity,'read') && reportKeys?.includes(key)`. Thay 2 chỗ lọc tay (`use-report-overview.ts`,
  `report-overview-page.tsx`) — cả hai giờ đọc thêm `useNavContext().reportKeys`.

## Test (tất cả PASS, chạy 2 lần ổn định)
- `report-catalog.test.ts`: thêm nhóm "key (ReportKey backend) đồng bộ với statuses.ts" — key duy
  nhất, tập `String(key)` khớp hệt `REPORT_KEY[].value` sinh từ backend (thiếu/thừa đỏ ngay),
  nhãn khớp nhãn `REPORT_KEY`, mục menu từng báo cáo có `reportKeys == [key]`, Tổng quan có union
  đủ 13 khóa.
- `filter-visible-reports.test.ts` (mới, 10 ca): rỗng/undefined/khóa lạ/trùng/gác kép thiếu một
  vế (entity hoặc key)/nhiều báo cáo cùng key khác entity.
- `module-visibility.test.ts`: thêm describe `reportKeys — gác kép báo cáo (fail-closed)` (9 ca) —
  ẩn khi ctx thiếu/rỗng/không khớp; hiện khi đủ cả hai; có key mà thiếu entity vẫn ẩn (gác kép);
  `canAccessRoute('/report/work', ...)` false khi thiếu khóa 13, true khi có; `firstAccessibleNavPath`
  bỏ qua báo cáo chưa gán; `canOpenModule` trên `reportModule` THẬT (không phải fixture) false khi
  `reportKeys: []` dù mọi entity đọc được — chính là bẫy "điều hướng mặc định mở" được yêu cầu
  chứng minh: trước khi thêm nhánh gác trong `itemAllowed`, test này đỏ (đã thử tắt nhánh, xác
  nhận đỏ, rồi gắn lại xanh).
- `use-permission.test.ts`: thêm describe `useNavContext` (5 ca) — hồ sơ cũ thiếu `report_keys`
  trả `undefined` (không phải `[]`), mảng rỗng giữ nguyên rỗng, tham chiếu ổn định giữa 2 lượt
  render không đổi state.
- `report-overview-page.test.tsx`: thêm mock `useNavContext` (mặc định `ALL_REPORT_KEYS` = 1..13
  để các ca cũ không phải sửa logic), thêm describe mới "gác kép: entity đọc được nhưng chưa được
  GÁN báo cáo nào" — `reportKeys: []` thì `apiGet` KHÔNG bị gọi lần nào dù đọc được mọi entity;
  được gán đúng 1/2 khóa cùng entity thì chỉ báo cáo đó lộ, báo cáo kia (cùng entity, khác key) ẩn.
- `report-overview-kpi-strip.test.tsx`: chỉ cần thêm `key: 1` vào fixture `buildReport` cho đúng
  kiểu — component này nhận `entries` đã lọc sẵn từ `ReportOverviewPage`, không tự gọi hook nên
  không cần mock `useNavContext`.

Lệnh: `npx vitest run src/modules/report src/app/router src/core/auth` → 26 tệp, 276 passed + 1
expected fail (CÓ SẴN, không do phase này — `use-permission.test.ts::it.fails` bẫy `!!"false"`).
`npm run typecheck` 0 lỗi (cả cây, kể cả phần phase 06 đang sửa dở). `npm run lint` 0 lỗi, 29
warning CÓ SẴN (không thuộc file nào tôi sửa).

## File đã tạo / sửa
Tạo: `src/modules/report/utils/filter-visible-reports.ts` (+test).
Sửa: `src/core/auth/auth-types.ts`, `src/core/authorization/use-permission.ts` (+test),
`src/app/router/module-definition.ts`, `src/app/router/module-visibility.ts` (+test),
`src/modules/report/config/report-catalog.ts`, `report-catalog-{procurement,hr,admin,document,
work}.ts`, `src/modules/report/routes.tsx`, `src/modules/report/hooks/use-report-overview.ts`,
`src/modules/report/pages/report-overview-page.tsx` (+test), `src/modules/report/components/
report-overview-kpi-strip.test.tsx` (fixture).

Không chạm `statuses.ts`, `src/modules/system/**`, `src/shared/constants/query-keys.ts` (sở hữu
agent 06).

## Vướng mắc khi làm
Edit tool bị lệch normalization Unicode (NFC/NFD) với vài đoạn comment tiếng Việt có dấu tổ hợp —
`old_string` khớp 100% theo mắt vẫn báo "not found". Vá bằng cách neo `old_string` vào đoạn ASCII
thuần quanh đó, hoặc viết hẳn qua Python (`io.open(..., encoding="utf-8")`) khi đoạn chèn toàn
tiếng Việt có dấu. Không ảnh hưởng nội dung cuối cùng — đã soát lại bằng `Read` sau mỗi lần ghi.

**Status:** DONE
**Summary:** Gác kép menu/route/Tổng quan theo `report_keys` xong đủ 4 todo của phase 05. Bẫy
"điều hướng mặc định mở" đã chứng minh bắt được qua test trên `reportModule` thật. 3 cổng xanh
(typecheck 0, lint 0 lỗi/29 warning có sẵn, vitest 276 passed + 1 expected-fail có sẵn).
**Concerns:** Không có — hợp đồng backend khớp đúng 1-1 (13 key, thứ tự PURCHASE_REPORT..WORK),
không cần chỉnh gì ngoài kế hoạch.
