# Phase 05 — FE: gác menu, route (gõ thẳng URL), Tổng quan theo `report_keys`

**Ưu tiên:** P1 · **Effort:** 2.5h · **Trạng thái:** done · **Phụ thuộc:** 01 (`REPORT_KEY` trong `statuses.ts`), hợp đồng `report_keys` của 02

## Context
- `src/modules/report/config/report-catalog*.ts`, `routes.tsx`, `hooks/use-report-overview.ts`, `pages/report-overview-page.tsx:68`
- `src/app/router/module-definition.ts` (`ModuleNavItem`), `module-visibility.ts` (`NavContext`, `itemAllowed`, `canAccessRoute`)
- `src/core/authorization/use-permission.ts::useNavContext`, `src/core/auth/auth-types.ts::AuthUser`
- Bẫy «điều hướng mặc định MỞ»: `canAccessRoute` trả true khi không mục nào khớp — mọi route báo cáo ĐÃ có mục menu cùng path (test hiện có canh) nên gác qua mục menu là đủ.

## Luồng dữ liệu
`/auth/me.report_keys` → `authStore.user.report_keys` → `useNavContext().reportKeys` → `itemAllowed` (menu · launcher · `canAccessRoute` · `firstAccessibleNavPath`) + `filterVisibleReports` (Tổng quan, Danh sách báo cáo, dải KPI).

## Thiết kế
- `AuthUser.report_keys?: number[]`.
- `useNavContext()` trả thêm `reportKeys` (đọc thẳng mảng từ store, tham chiếu ổn định).
- `NavContext.reportKeys?: readonly number[]`; `ModuleNavItem.reportKeys?: readonly number[]` — «chỉ hiện khi ctx chứa ÍT NHẤT MỘT khóa; xét SAU luật entity (gác kép)». Trong `itemAllowed`: sau `if (!baseOk) return false` thêm
  `if (item.reportKeys && !item.reportKeys.some((k) => ctx.reportKeys?.includes(k))) return false` — thiếu ctx ⇒ ĐÓNG (fail-closed, ngược với mặc định mở của mục không khai).
- `ReportCatalogEntry.key: number` + chú thích «= `ReportKey` backend, không đổi/không tái dùng»; khai `key` cho 13 mục ở 5 tệp nhóm.
- `routes.tsx`: mục báo cáo `reportKeys: [r.key]`; mục Tổng quan `reportKeys: REPORT_CATALOG.map((r) => r.key)` (giữ `entities`).
- `src/modules/report/utils/filter-visible-reports.ts`: `filterVisibleReports(catalog, can, reportKeys)` = `can(r.entity,'read') && reportKeys.includes(r.key)`; dùng ở `use-report-overview.ts` và `report-overview-page.tsx:68` (thay 2 chỗ lọc `can` hiện có — DRY).
- Ca lệch cặp (có entity A + được gán báo cáo B, không ai đủ cả hai) → mục Tổng quan vẫn hiện nhưng trang rỗng → dùng trạng thái rỗng sẵn có. Chấp nhận, ghi chú trong code.
- Không cần query key mới (dữ liệu nằm trong `auth.me`).

## Test (cạnh tệp)
- `report-catalog.test.ts`: `key` duy nhất; tập `String(key)` == tập `REPORT_KEY[].value` (sinh từ backend) — thiếu/thừa là đỏ; `label` catalog == `label` của `REPORT_KEY`; mục menu mỗi báo cáo có `reportKeys == [key]`; Tổng quan có đủ mọi khóa.
- `module-visibility.test.ts`: mục có `reportKeys` → ẩn khi ctx thiếu `reportKeys`, khi mảng rỗng, khi không chứa khóa; hiện khi chứa khóa VÀ có entity; có khóa mà thiếu entity → ẩn (gác kép); `canAccessRoute('/report/work')` false khi thiếu khóa; `firstAccessibleNavPath` bỏ qua báo cáo không được gán; `canOpenModule` báo cáo false khi `reportKeys=[]`.
- `filter-visible-reports.test.ts`: rỗng/undefined/khóa lạ (999)/khóa trùng; entity thiếu.
- `report-overview-page.test.tsx` / `report-overview-kpi-strip.test.tsx`: cập nhật dữ liệu giả của auth để có `report_keys`; thêm ca không gán gì → không gọi `/summary` nào (khẳng định `reportAnalyticsApi.get` không bị gọi).

## Lệnh
`typecheck` + `lint` cả cây; `npx vitest run src/modules/report src/app/router src/core/authorization`.

## Sở hữu tệp
Sửa: `src/modules/report/**` (config, routes, hook, page, test), `src/app/router/module-definition.ts`, `module-visibility.ts`(+test), `src/core/auth/auth-types.ts`, `src/core/authorization/use-permission.ts`. Tạo: `src/modules/report/utils/filter-visible-reports.ts`(+test). KHÔNG chạm `statuses.ts` (phase 01 sinh).

## Todo
- [x] AuthUser + useNavContext + NavContext/ModuleNavItem
- [x] key cho 13 mục catalog + routes
- [x] filterVisibleReports + thay 2 chỗ lọc
- [x] test

## Tiêu chí xong
Local: tài khoản không gán → không thấy thẻ Báo cáo ở launcher, gõ `/report/work` ra trang 403; admin thấy đủ 13. 3 cổng xanh.

## Rủi ro
| Rủi ro | K×T | Giảm thiểu |
|---|---|---|
| User lưu trong localStorage (trước deploy) thiếu `report_keys` → mất báo cáo tới khi đăng nhập lại/làm mới phiên | Cao×Thấp | Fail-closed là đúng chiều an toàn; ghi trong thông báo deploy «đăng xuất/đăng nhập lại» |
| Gán xong người được gán chưa thấy ngay | Cao×Thấp | Cùng hành vi với ma trận quyền hiện nay; ghi trong hướng dẫn |
| Thêm báo cáo mới quên `key` | Thấp×TB | TS bắt buộc trường + test khớp tập khóa |
