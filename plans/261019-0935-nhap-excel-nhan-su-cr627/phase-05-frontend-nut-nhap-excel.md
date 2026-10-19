# Pha 05 — Frontend: nút «Nhập Excel» (v2) + ẩn Import CSV (v1)

**Ưu tiên:** P1 · **Trạng thái:** pending · **Công:** 0.5d · **Chặn bởi:** — (chạy song song 01–04)

## frontend-v2
`employee-list-page.tsx` đã 276 dòng → KHÔNG nhồi state hộp thoại vào trang; tách component.

- Tạo `frontend-v2/src/modules/hr/components/employee-import-button.tsx` (~50 dòng):
  - Hiện khi `can('import','create') && can('import','read') && (can('employee','create') || can('employee','write'))`
    — cần `import.read` vì sau khi tạo lô sẽ sang `/system/imports/{id}` (GET lô gác `import.read`;
    nhớ bẫy «gác điều hướng mặc định MỞ»). Dùng `usePermission().can` (PermissionGate chỉ nhận 1 cặp).
  - `Button variant="outline"` icon `FileUp` (lucide) nhãn «Nhập Excel»; khổ hẹp `max-md:w-full`.
  - `<ImportUploadDialog lockedModule={IMPORT_MODULE_EMPLOYEE} onCreated={(id) => navigate(appRoutes.system.importDetail(id))} />`
    (import chéo phân hệ `@/modules/system/...` được phép — rules/components.md).
- Sửa `frontend-v2/src/modules/hr/pages/employee-list-page.tsx` (~181-188): bọc `actions` bằng
  `<div className="flex gap-2 max-md:flex-col">` gồm `<EmployeeImportButton />` + nút «Thêm mới» cũ.
- `import-meta.ts`: **không đổi** (EMPLOYEE=12 đã có, `hasTemplate: true`, phân hệ `hr`).
- KHÔNG thêm «Xuất Excel» ở màn này: CR-172 đã gỡ nút xuất từng màn, xuất tập trung ở `/system/exports`
  có ghi `ExportLog`; `/api/employees/export/xlsx` không ghi log và chỉ 8 cột (câu hỏi treo #2).
- Tạo `frontend-v2/src/modules/hr/components/employee-import-button.test.tsx`:
  1. đủ quyền → hiện nút; 2. thiếu `import.create` → ẩn; 3. chỉ `employee.write` (không create) → hiện;
  4. thiếu cả `employee.create`/`write` → ẩn; 5. bấm → hộp thoại mở, ô đối tượng khóa «Nhân sự»;
  6. `onCreated(42)` → điều hướng `/system/imports/42`. (Mock `usePermission` + `useUploadImport` theo
  khuôn test sẵn có trong `modules/hr/components/*.test.tsx`.)

## frontend (v1, đóng băng — sửa tối thiểu)
- `frontend/src/config/cruds.tsx`: thêm `importDisabled?: boolean` vào kiểu cấu hình (cạnh
  `importExport?`, ~dòng 62); đặt `importDisabled: true` cho `employees` (~395) và `departments` (~690).
- `frontend/src/components/CrudList.tsx:415-416`: chỉ vẽ nút «Import CSV» + `<input type=file>` khi
  `!cfg.importDisabled`. «Export CSV» giữ nguyên.

## Todo
- [ ] `employee-import-button.tsx` + test
- [ ] Gắn vào `employee-list-page.tsx`
- [ ] v1: `importDisabled` cho 2 màn

## Cổng kiểm (chỉ chạy)
```bash
docker compose exec -T erp npm run typecheck
docker compose exec -T erp npm run lint
docker compose exec -T erp npx vitest run src/modules/hr/components/employee-import-button.test.tsx src/modules/hr/pages
```
v1: `docker compose exec -T web npx tsc --noEmit` — baseline đúng 4 lỗi cũ, không thêm.

## Thành công khi
typecheck/lint 0 lỗi; 6 test xanh; v1 màn Nhân sự & Phòng ban không còn «Import CSV», vẫn còn «Export CSV».

## Rủi ro
| Rủi ro | K×T | Giảm thiểu |
|---|---|---|
| Hàng nút tràn ở khổ hẹp | TB×Thấp | `max-md:flex-col` + `w-full`; kiểm bằng emulate 390px (không resize) |
| Người dùng bấm «Ghi thật» ngay | Thấp×TB | Dialog đã mặc định «Chạy thử» (`useState(IMPORT_MODE_DRY_RUN)`); không sửa dialog dùng chung |
