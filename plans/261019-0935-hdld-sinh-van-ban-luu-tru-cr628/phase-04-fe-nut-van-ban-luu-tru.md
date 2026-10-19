# Phase 04 — FE: nút «Văn bản lưu trữ»

**Ưu tiên:** P3 · **Trạng thái:** pending · **Effort:** 1.5h · **Phụ thuộc:** 03 (chỉ cần hợp đồng API: `document_id`, `can_open_document`)
**Sở hữu tệp:** `frontend-v2/src/modules/hr/{types/labor-contract.ts, components/labor-contract-row-actions*.tsx, components/labor-contract-fixture.ts}`

## Context
- `frontend-v2/.claude/rules/*.md` (icons: `lucide-react`; testing: vitest theo thư mục).
- `labor-contract-row-actions.tsx` (149 dòng) — hiện/ẩn theo cờ BACKEND (`can_*`), không tự ghép `can()`.
- Đường chi tiết văn bản: `appRoutes.document.documentDetail(id)`; khuôn mở tab mới: `document-needs-review-banner.tsx:112` (`window.open(..., '_blank', 'noopener')`).
- Tab HĐ nằm TRONG `<form>` hồ sơ ⇒ không điều hướng tại chỗ (mất dữ liệu đang sửa) → mở tab mới; nút `type="button"`.

## Yêu cầu
- Hiện nút icon `Archive` «Mở bản lưu trữ ở Văn bản» khi `row.can_open_document && row.document_id > 0`.
- Bấm ⇒ mở tab mới `documentDetail(row.document_id)`; `stopPropagation` (đã có ở div cha).
- Không đổi luật tải bản ký (giữ `SIGNED_FILE_ACCEPT`).

## Tệp
- Sửa: `hr/types/labor-contract.ts` (+`document_id: number`, `can_open_document: boolean`)
- Sửa: `hr/components/labor-contract-fixture.ts` (mặc định `0` / `false`)
- Sửa: `hr/components/labor-contract-row-actions.tsx` (+1 nút, ~10 dòng; không thêm handler prop — tự gọi `window.open`)
- Sửa: `hr/components/labor-contract-row-actions.test.tsx`

## Test (vitest)
1. `can_open_document=true, document_id=12` ⇒ có nút; bấm ⇒ `window.open` gọi với đường chứa `/12`, `'_blank'`, `'noopener'`.
2. `can_open_document=false` ⇒ không có nút.
3. `document_id=0` (dù `can_open_document=true`) ⇒ không có nút.
4. Bấm nút không kích `onRowClick` (đã có test tương tự cho nút khác — mở rộng).

## Cổng
`docker compose exec -T erp npm run typecheck` · `npm run lint` · `npx vitest run src/modules/hr` — 0 lỗi, không thêm cảnh báo.

## Tiêu chí xong
- Ba cổng xanh; thủ công: HR mở hồ sơ → tab Hợp đồng → nút mở đúng văn bản; tài khoản không có `document.read` không thấy nút.

## Rủi ro
| Rủi ro | K×Ả | Giảm thiểu |
|---|---|---|
| Fixture thiếu trường mới ⇒ typecheck đỏ ở test khác | TB × Thấp | Sửa `labor-contract-fixture.ts` dùng chung |
