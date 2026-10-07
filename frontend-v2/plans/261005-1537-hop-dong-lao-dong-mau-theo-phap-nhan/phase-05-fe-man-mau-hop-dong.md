# Phase 05 — FE màn «Mẫu hợp đồng»

## Context Links
- `frontend-v2/.claude/rules/*.md`, `frontend-v2/docs/ui/table.md`, `docs/ui/date.md`
- `src/modules/hr/routes.tsx` (nav + routes), `src/shared/constants/app-routes.ts`, `src/shared/constants/query-keys.ts` (`hr.*`)
- Dùng lại: `@/shared/data-table`, `@/shared/ui/file-dropzone`, `@/shared/ui/page-header`, `labelOf` + `LABOR_CONTRACT_TYPE` (`@/shared/constants/statuses`), `useCompanies` (`hr/hooks/use-companies.ts`)
- Memory: «Gác điều hướng mặc định MỞ» — route phải có mục menu khai `entity`, trang vẫn tự kiểm `can()`

## Overview
Priority P2. Status done (05/10/2026). Màn `/hr/labor-contract-templates`: danh sách mẫu theo pháp nhân, tải lên/thay tệp/tải về/ngừng dùng/xóa, bảng hướng dẫn biến. Phase này **sở hữu** mọi tệp FE dùng chung của tính năng (types, api, query-keys, app-routes) để phase 06 chỉ đọc.

## Requirements
- Nav: mục «Mẫu hợp đồng» (icon `FileSignature`), `entity: 'labor_contract_template'`, `group: 'Danh mục'`, ngay dưới «Chức vụ».
- Bộ lọc: pháp nhân (ô chọn), loại HĐ, trạng thái dùng; ô tìm tên. Cột: ID · Tên mẫu · Pháp nhân · Loại HĐ · Tệp gốc · Số HĐ đã dùng · Trạng thái · Cập nhật.
- Hộp tải lên: Tên, Pháp nhân (bắt buộc, chỉ pháp nhân đọc được), Loại HĐ, Ghi chú, Tệp `.docx` (`FileDropzone`, accept `.docx`, ≤10MB). Lỗi 422 `unknown` → hiện danh sách biến lạ NGAY trong hộp (không chỉ toast) + gợi ý «gõ lại biến liền một lần, không định dạng giữa chừng».
- Hành động dòng: Tải tệp · Thay tệp · Ngừng/Bật dùng · Xóa (409 → câu backend). Ẩn theo `can('labor_contract_template', 'write'|'delete')`.
- Nút «Danh sách biến» mở Sheet/Dialog đọc `GET /placeholders`, nhóm theo `group`, mỗi dòng có nút sao chép `{{ key }}` (icon `Copy`). KHÔNG chép danh sách biến sang TS.

## Related Code Files
- Create: `src/modules/hr/types/labor-contract.ts` (LaborContract, LaborContractTemplate, Placeholder, payloads), `api/labor-contract-template-api.ts`, `api/labor-contract-api.ts` (cả 2 api ở phase này để 06 không đụng chung), `hooks/use-labor-contract-templates.ts`, `config/labor-contract-template-columns.tsx`, `pages/labor-contract-template-list-page.tsx`, `components/labor-contract-template-upload-dialog.tsx`, `components/labor-contract-placeholder-guide-dialog.tsx`, test cạnh tệp
- Modify: `src/shared/constants/query-keys.ts` (`hr.laborContractTemplates(params)`, `hr.laborContractPlaceholders()`, `hr.employeeLaborContracts(id)` = `['hr','employees',id,'labor-contracts']`, `hr.employeeLaborContractTemplates(id, type)`), `src/shared/constants/app-routes.ts` (`hr.laborContractTemplates`), `src/modules/hr/routes.tsx`

## Implementation Steps
1. Types + 2 api (multipart qua `httpClient`, KHÔNG đặt tay `Content-Type`; tải tệp `responseType: 'blob'` + đọc tên từ `Content-Disposition`). Kiểm có sẵn helper tải blob ở `@/core/api`/`shared/utils` trước khi viết.
2. Query keys + app route + nav + route lazy.
3. Trang danh sách (DataTable, `storageKey: 'hr.labor-contract-templates'`).
4. Hộp tải lên (`react-hook-form` + zod) dùng chung cho «Thay tệp» (chế độ chỉ tệp).
5. Hộp hướng dẫn biến.
6. Vitest: hộp tải lên hiện danh sách biến lạ từ lỗi 422; nút ẩn khi thiếu quyền; bộ chuyển payload (company_id 0 → chặn); hướng dẫn biến sao chép đúng `{{ ho_ten }}`.

## Todo
- [x] types/api/keys/routes · [x] trang danh sách · [x] hộp tải lên/thay · [x] hộp hướng dẫn biến · [x] vitest

## Success Criteria
`npm run typecheck` 0 lỗi, `npm run lint` 0 lỗi (không thêm cảnh báo), `npx vitest run src/modules/hr` xanh. Tài khoản không có khóa không thấy menu, gõ URL → trang báo thiếu quyền, API 403.

## Risk Assessment
| Rủi ro | K×T | Giảm thiểu |
|---|---|---|
| Route mở cho mọi người | Trung×Thấp | mục nav khai entity + trang kiểm `can()`; BE vẫn chặn |
| Tệp >200 dòng | Trung×Thấp | tách columns/dialog/guide riêng |

## Security
FE chỉ ẩn nút; quyền thật ở BE. Không dựng URL storage trực tiếp.

## Next
Phase 06.
