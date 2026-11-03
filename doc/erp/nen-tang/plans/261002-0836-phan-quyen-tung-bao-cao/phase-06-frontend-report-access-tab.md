# Phase 06 — FE: tab «Báo cáo» trong Phân quyền tài khoản

**Ưu tiên:** P2 · **Effort:** 3h · **Trạng thái:** done · **Phụ thuộc:** 02 (API), 04 (picker ở shared)

## Context
- `src/modules/system/pages/role-permission-page.tsx` (244 dòng, Tabs `roles`/`users` ghi `?tab=`; mục menu gác `role` + `manage: true`)
- `src/shared/access-subject/*` (phase 04), `src/modules/hr/hooks/use-access-subject-options.ts`
- `docs/ui/table.md` (DataTable), `src/shared/constants/query-keys.ts` (nhánh `system`)
- Bẫy bao-CR-492 ở trang này (khởi tạo state từ dữ liệu có sẵn) — tab mới KHÔNG dùng chung state với tab vai trò.

## Hợp đồng API (từ phase 02)
`GET /api/report-access` → `ReportAccessItem[] {key,label,group,grants: ReportAccessGrant[]}`; `POST /api/report-access/{key}/grants {subjects, effect, reason}` → `{created,updated,skipped}`; `DELETE /api/report-access/grants/{id} {reason}`.

## Thiết kế
- `types/report-access.ts` — kiểu theo hợp đồng.
- `api/report-access-api.ts` — `apiGet/apiPost/apiDelete` từ `@/core/api`.
- `hooks/use-report-access.ts` — `useReportAccessList()` (key `queryKeys.system.reportAccess()` — thêm vào `query-keys.ts`), `useGrantReportAccess()`, `useRevokeReportAccess()`; thành công → invalidate `system.reportAccess` + `auth.me` (phòng admin vừa gán/cấm chính mình) + toast `sonner`.
- `components/report-access-tab.tsx` — `DataTable`, dòng sắp theo nhóm (cột «Phân hệ» đầu, hoặc tiêu đề nhóm nếu DataTable hỗ trợ — đọc `docs/ui/table.md`); cột: Báo cáo · Được xem (chip chủ thể CHO PHÉP) · Bị cấm (chip màu `destructive`) · nút «Sửa» (icon `Pencil`, chỉ khi `can('role','write')`). Báo cáo 0 dòng CHO PHÉP → nhãn «Chưa ai xem được».
- `components/report-access-dialog.tsx` — tiêu đề tên báo cáo; khối 1: danh sách dòng còn sống (avatar + tên + loại + Cho phép/Cấm + nút thu hồi có ô lý do, dùng `ConfirmIconButton`/hộp xác nhận sẵn có); khối 2: `AccessSubjectPicker` + chọn Cho phép/Cấm (RadioGroup/ToggleGroup shadcn) + lý do (≤500, đếm ký tự) + nút «Thêm». Chú thích ngay trong hộp: «Được gán chỉ mở báo cáo; số liệu vẫn theo quyền phân hệ gốc. Cấm thắng cho phép.»
- `role-permission-page.tsx`: thêm `<TabsTrigger value="reports">Báo cáo</TabsTrigger>` + `<TabsContent value="reports"><ReportAccessTab /></TabsContent>`, chỉ dựng khi `can('role','read')`. Trang đã >200 dòng: chỉ thêm ~8 dòng, KHÔNG tách lại tab vai trò trong phạm vi này (rủi ro CR-492).
- Không import `modules/report` (nhãn/nhóm lấy từ API) → system không dính ruột report.

## Test (cạnh tệp, mock ở `@/core/api`)
- `report-access-tab.test.tsx`: hiện đủ 13 dòng theo nhóm; dòng 0 cho phép → «Chưa ai xem được»; không `role.write` → không có nút Sửa; danh sách rỗng/API lỗi → trạng thái lỗi, không trắng trang.
- `report-access-dialog.test.tsx`: chọn 2 chủ thể + Cấm + lý do → gọi POST đúng `{subjects:[…2], effect:2, reason}`; nút Thêm vô hiệu khi chưa chọn ai; lý do 501 ký tự bị chặn; thu hồi gọi DELETE đúng id; dòng cấm hiển thị khác dòng cho phép (theo text/role, không theo class).
- `role-permission-page` (nếu đã có test): tab «Báo cáo» hiện khi có `role.read`.

## Lệnh
`typecheck` + `lint`; `npx vitest run src/modules/system src/shared/access-subject`.

## Sở hữu tệp
Tạo: `src/modules/system/{types/report-access.ts,api/report-access-api.ts,hooks/use-report-access.ts,components/report-access-tab.tsx,components/report-access-dialog.tsx}` (+test). Sửa: `role-permission-page.tsx`, `src/shared/constants/query-keys.ts` (chỉ thêm 1 khóa). Mỗi tệp mới <200 dòng (tách `report-access-grant-list.tsx` nếu hộp thoại phình).

## Todo
- [x] types/api/hooks + query key
- [x] tab + hộp thoại
- [x] gắn tab vào trang
- [x] test

## Tiêu chí xong
Local bằng admin: cấp cho phòng X → tài khoản phòng X (đăng nhập lại) thấy báo cáo; thêm Cấm cho 1 người trong phòng → người đó mất; thu hồi Cấm → thấy lại. 3 cổng xanh.

## Rủi ro
| Rủi ro | K×T | Giảm thiểu |
|---|---|---|
| Tự cấm chính mình (admin) | Thấp×Thấp | Màn cấu hình không gác báo cáo → tự thu hồi được; hộp thoại cảnh báo khi chủ thể chứa chính mình/vai trò mình (tùy chọn) |
| UI không theo quy ước (emoji, class nối chuỗi) | Thấp×Thấp | lucide + `cn()`; review |
