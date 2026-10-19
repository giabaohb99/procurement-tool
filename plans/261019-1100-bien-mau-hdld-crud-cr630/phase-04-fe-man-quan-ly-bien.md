# Phase 04 — FE: màn quản lý «Danh sách biến»

**Ưu tiên:** P2 · **Status:** pending · **Effort:** 4h · **Phụ thuộc:** 02 (hợp đồng API, làm được trước khi 02 merge nếu theo đúng bảng endpoint) · **Song song với:** 03

## Bối cảnh
- Nút «Danh sách biến» ở `frontend-v2/src/modules/hr/components/labor-contract-template-catalog.tsx` (nằm trong `/document/settings?tab=templates&kind=labor-contract`) đang mở `labor-contract-placeholder-guide-dialog.tsx` (chỉ xem).
- Luật: DataTable + `docs/ui/table.md`; `usePageResetOnFilterChange`; câu rỗng phân biệt lọc/chưa có; nút trong form `type="button"`; chặn bấm đúp bằng `useRef`; ô chỉ xem dùng `ReadOnlyValue`; query key từ `shared/constants/query-keys`; không barrel; test cạnh tệp.
- Gác điều hướng mặc định MỞ: route phải nằm dưới tiền tố `/hr/labor-contract-templates` (đã có mục menu ẨN gác `labor_contract_template`) + trang tự kiểm `can(...,'read')`.

## Thiết kế UI
- **Trang riêng** `/hr/labor-contract-templates/variables` (`appRoutes.hr.laborContractVariables`), nút «Danh sách biến» đổi thành `navigate(...)`. Lý do: bảng ~150 dòng + bộ lọc + hộp sửa lồng — hộp thoại trong hộp thoại là kém; trang riêng có URL lọc chia sẻ được. Đầu trang có nút «← Mẫu hợp đồng» về `appRoutes.document.laborContractTemplates`.
- DataTable cột: `{{ mã }}` (font mono + `CopyButton` chép `{{ mã }}`) · Tên hiển thị · Nhóm · Kiểu (badge; hệ thống «—») · Ví dụ · Bắt buộc khi sinh · Số mẫu đang dùng · Trạng thái (Đang dùng / Ngừng / Ẩn) · thao tác.
- Bộ lọc: tìm (mã/nhãn), Nguồn (Tất cả / Hệ thống / Tùy chỉnh), Kiểu, Trạng thái. Câu rỗng: «Không có biến nào khớp bộ lọc.» / «Chưa có biến tùy chỉnh. Bấm «Thêm biến».»
- Thao tác dòng (ẩn theo `can`): hệ thống — Sửa (nhãn/mô tả), Ẩn/Hiện; tùy chỉnh — Sửa, Ngừng dùng/Bật lại, Xóa (confirm; 409 http-client tự toast câu backend có số mẫu/HĐ).
- **Hộp thêm/sửa** `labor-contract-variable-form-dialog.tsx` (react-hook-form + zod): Mã (gõ chữ thường, gợi ý `snake_case`; khi `code_locked` hoặc biến hệ thống ⇒ `ReadOnlyValue` + câu «Đang dùng trong N mẫu / M hợp đồng — không đổi được mã»), Tên hiển thị *, Mô tả, Kiểu (Select từ bộ mã sinh — khóa khi `code_locked`), Ví dụ, Giá trị mặc định (ô đổi theo kiểu — dùng chung ô của phase 05), Bắt buộc khi sinh tệp (Switch), Thứ tự, Đang dùng (Switch). Biến hệ thống chỉ hiện Tên/Mô tả/Ẩn khỏi danh sách. Mở để sửa ⇒ gọi `GET /{id}` lấy `usage` + `code_locked`.
- Zod FE chỉ kiểm hình dạng (regex mã, độ dài khớp backend 40/200/500/255/2000, thứ tự 0..9999) — backend là chuẩn, KHÔNG chép danh sách từ cấm/mã hệ thống sang TS.
- Xóa `labor-contract-placeholder-guide-dialog.tsx` + test (DRY: trang mới thay thế; người chỉ có `read` thấy bảng chỉ xem + nút chép). Khung chèn biến CR-606 giữ nguyên (đọc `/placeholders`, nay động).

## Tệp
- Tạo (`frontend-v2/src/modules/hr/`): `types/labor-contract-variable.ts`, `api/labor-contract-variable-api.ts`, `hooks/use-labor-contract-variables.ts`, `config/labor-contract-variable-columns.tsx`, `components/labor-contract-variable-row-actions.tsx`, `components/labor-contract-variable-form-dialog.tsx`, `components/labor-contract-variable-value-input.tsx` (ô nhập theo kiểu — dùng lại ở phase 05), `schemas/labor-contract-variable-schema.ts`, `pages/labor-contract-variables-page.tsx` + test cạnh mỗi tệp có hành vi
- Sửa: `hr/routes.tsx` (route lazy), `shared/constants/app-routes.ts`, `shared/constants/query-keys.ts` (`hr.laborContractVariables(params)`, `hr.laborContractVariable(id)`, `hr.laborContractVariableInputFields()` — đều dưới `['hr', ...]` để `hr.all` quét), `hr/components/labor-contract-template-catalog.tsx` (+ test), `app/router/module-visibility.test.ts` (1 ca)
- Xóa: `hr/components/labor-contract-placeholder-guide-dialog.tsx`, `.test.tsx`
- Sở hữu: phase 04 độc quyền các tệp trên; phase 05 chỉ IMPORT `labor-contract-variable-value-input.tsx` / types / hook, không sửa.

## Các bước
1. Types + API + hooks (mutation `onSuccess` quét `queryKeys.hr.all` ⇒ `/placeholders` của khung chèn cũng mới).
2. Ô nhập theo kiểu `LaborContractVariableValueInput` (TEXT `Input` · MULTILINE `Textarea` · NUMBER `Input inputMode="decimal"` đổi `,`→`.` khi gửi · DATE `DatePicker` · MONEY `NumberInput`).
3. Cột + thao tác dòng + hộp form + trang; route + app-routes; nút catalog.
4. Gate: `typecheck`, `lint`, `vitest run src/modules/hr src/app/router`.

## Test (vitest)
- `labor-contract-variables-page.test.tsx`: thiếu `read` ⇒ câu không có quyền, không gọi API; chỉ `read` ⇒ không có nút Thêm/Sửa/Xóa, vẫn có nút chép; dòng hệ thống không có Xóa; câu rỗng khác nhau khi lọc / không lọc; đổi bộ lọc về trang 1.
- `labor-contract-variable-form-dialog.test.tsx`: biến hệ thống chỉ 3 ô; `code_locked` ⇒ mã + kiểu chỉ đọc (bôi đen được, không `disabled`); mã «Ho_Ten»/«1abc»/41 ký tự ⇒ lỗi; bấm Lưu 3 lần liền ⇒ 1 lần gọi API; đổi kiểu ⇒ ô mặc định đổi loại ô.
- `labor-contract-variable-value-input.test.tsx`: mỗi kiểu ra đúng ô; số «1,5» gửi «1.5»; tiền âm/vượt 10^12 bị chặn.
- `labor-contract-template-catalog.test.tsx`: nút «Danh sách biến» điều hướng tới trang biến.
- `module-visibility.test.ts`: `/hr/labor-contract-templates/variables` gác bằng `labor_contract_template.read`.
```bash
docker compose exec -T erp npm run typecheck && docker compose exec -T erp npm run lint
docker compose exec -T erp npx vitest run src/modules/hr src/app/router/module-visibility.test.ts
```

## Tiêu chí xong
3 cổng xanh; bấm tay: thêm 1 biến mỗi kiểu, ngừng dùng, xóa bị chặn khi mẫu dùng, chép `{{ mã }}` dán vào Word đúng.

## Rủi ro
| Rủi ro | K×Ả | Giảm thiểu |
|---|---|---|
| Route mới lọt ngoài hàng rào menu ẩn ⇒ ai cũng vào | Thấp × TB | Đặt dưới tiền tố đã gác + test module-visibility + trang tự kiểm quyền |
| Nhãn hệ thống sửa xong khung chèn vẫn cũ (staleTime 10 phút) | TB × Thấp | Mutation quét `hr.all` |
| Bảng nhớ bố cục cũ trong localStorage | Thấp × Thấp | `storageKey` mới `hr.labor-contract-variables` |
