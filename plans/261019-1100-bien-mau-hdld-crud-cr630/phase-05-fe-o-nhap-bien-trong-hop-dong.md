# Phase 05 — FE: ô nhập biến tùy chỉnh trong hộp «Lập / Sửa hợp đồng»

**Ưu tiên:** P2 · **Status:** done · **Effort:** 2h · **Phụ thuộc:** 03 (`custom_values` ở API HĐ), 04 (ô nhập theo kiểu, hook `/input-fields`, types)

## Bối cảnh
- `hr/components/labor-contract-form-dialog.tsx` (108 dòng) + `labor-contract-form-dialog-fields.tsx` (164 dòng, sát trần 200) + `hr/schemas/labor-contract-schema.ts` (`buildContractFormDefaults`, `toLaborContractPayload`).
- Hộp nằm TRONG `<form>` trang hồ sơ ⇒ giữ `stopPropagation` (BẪY 1+4); ô con không được submit form cha khi Enter (Textarea an toàn, Input thì `onKeyDown` Enter ⇒ `preventDefault` nếu cần).

## Thiết kế
- Hook `useLaborContractVariableInputFields(open)` (phase 04) — chỉ nạp khi hộp mở; không có biến đang dùng ⇒ không vẽ gì (không khung rỗng).
- Component mới `labor-contract-custom-fields.tsx`: tiêu đề «Thông tin bổ sung cho mẫu», mỗi biến 1 ô `LaborContractVariableValueInput` theo `value_type`, thứ tự `sort_order`; nhãn + `RequiredMark` kèm chú «bắt buộc khi sinh tệp» nếu `is_required` (KHÔNG chặn lưu nháp — chỉ chặn ở bước sinh tệp, backend); `default_value` hiện làm chữ gợi ý «Để trống dùng mặc định: …» (KHÔNG điền sẵn vào ô — mặc định áp lúc sinh, phase 03); `description` làm `FormDescription`.
- Schema: `custom_values: z.record(z.string(), z.string())` (giá trị ô luôn là chuỗi; tiền đổi từ `NumberInput`); độ dài/định dạng mỗi ô kiểm ở ô nhập + backend là chuẩn (lỗi 422 http-client toast).
- `buildContractFormDefaults(employee, row)`: `custom_values: { ...(row?.custom_values ?? {}) }`.
- `toLaborContractPayload(values, mode, activeCodes)`: chỉ gửi khóa ∈ `activeCodes` (biến đang dùng), ô trống gửi `""` (backend xóa khóa); số đổi `,`→`.`. Khóa của biến ngừng dùng KHÔNG gửi ⇒ backend giữ giá trị cũ.
- Hộp «Sinh tệp» (`labor-contract-generate-dialog.tsx`): không đổi — 422 «Hợp đồng còn thiếu: …» do http-client toast. (Nếu toast bị cắt câu dài ⇒ ghi nhận, không xử lý ở CR này.)

## Tệp
- Tạo: `frontend-v2/src/modules/hr/components/labor-contract-custom-fields.tsx` + `.test.tsx`
- Sửa: `hr/components/labor-contract-form-dialog.tsx` (gọi hook, truyền `activeCodes`), `labor-contract-form-dialog-fields.tsx` (thêm 1 slot `customFields: ReactNode` — tránh vượt 200 dòng), `hr/schemas/labor-contract-schema.ts` + `.test.ts`, `hr/types/labor-contract.ts` (`LaborContract.custom_values`, `LaborContractPayload.custom_values`), `hr/components/labor-contract-fixture.ts` (`custom_values: {}`), `labor-contract-form-dialog.test.tsx`
- KHÔNG sửa tệp của phase 04.

## Test (vitest)
- `labor-contract-custom-fields.test.tsx`: không có biến ⇒ không vẽ khối; 5 kiểu ra đúng ô; biến bắt buộc có dấu sao + chú «bắt buộc khi sinh tệp»; mặc định hiện ở chữ gợi ý, ô vẫn rỗng; Enter trong ô chữ không submit form cha.
- `labor-contract-schema.test.ts`: `buildContractFormDefaults` chép `custom_values` của dòng (không dùng chung tham chiếu); `toLaborContractPayload` bỏ khóa ngừng dùng, ô trống ⇒ `""`, «1,5» ⇒ «1.5»; `null`/`undefined` `custom_values` của dòng cũ ⇒ `{}`.
- `labor-contract-form-dialog.test.tsx`: có biến ⇒ ô hiện; Lưu gửi `custom_values`; form cha KHÔNG bị submit (ca cũ giữ).
```bash
docker compose exec -T erp npm run typecheck && docker compose exec -T erp npm run lint
docker compose exec -T erp npx vitest run src/modules/hr
```

## Tiêu chí xong
3 cổng xanh; bấm tay: lập HĐ nhập biến → Sinh tệp → .docx có giá trị đúng định dạng; để trống biến bắt buộc → Sinh tệp báo thiếu đúng nhãn; sửa giá trị → tệp cũ mất, phải sinh lại.

## Rủi ro
| Rủi ro | K×Ả | Giảm thiểu |
|---|---|---|
| Gửi lại khóa của biến ngừng dùng ⇒ 422 khó hiểu | TB × TB | Lọc theo `activeCodes` + test |
| Hộp dài khi nhiều biến | TB × Thấp | `DialogContent` đã `max-h-[90vh] overflow-y-auto` |
| Người chỉ có `labor_contract.write` (không `template.read`) không thấy ô | Thấp × TB | `/input-fields` mở cho `labor_contract.create/write` (phase 02) |
