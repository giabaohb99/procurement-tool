# Phase 04 — FE: nâng ô chọn chủ thể (người/phòng/pháp nhân/vai trò) lên `src/shared/`

**Ưu tiên:** P2 · **Effort:** 2h · **Trạng thái:** done · **Phụ thuộc:** — (song song 01-03)

## Context
- `modules/document/components/folder-share-subject-picker.tsx` (239 dòng, gọi thẳng 4 hook của `modules/hr`), `access-subject-chips.tsx`, `access-subject-avatar.tsx`, 2 tệp test picker
- `modules/document/types/document-access.ts` (`SUBJECT_KIND`, `SUBJECT_KIND_LABELS`, `EFFECT`, `EFFECT_LABELS`) — 13 tệp dùng
- Luật: module không import ruột module khác; `shared/` KHÔNG được import `modules/`.

## Vấn đề
Picker gọi `useEmployees/useDepartments/useCompanies/useRoles` của `modules/hr` → không bê nguyên sang `shared/` được.

## Thiết kế
- `src/shared/access-subject/subject-kind.ts` — chuyển hằng `SUBJECT_KIND`, `SUBJECT_KIND_LABELS`, `EFFECT`, `EFFECT_LABELS`, kiểu `SubjectKind`, `MixedSubject`, `SubjectOption {subject_kind, subject_id, label}`.
- `src/shared/access-subject/access-subject-picker.tsx` — bản THUẦN UI của `FolderShareSubjectPicker`: nhận `options: SubjectOption[]` (+ `loading?`) qua prop thay vì tự gọi hook; giữ nguyên lọc không dấu, nút lọc loại, chọn nhiều. Tách `access-subject-picker-options.ts` nếu tệp >200 dòng.
- `src/shared/access-subject/access-subject-chips.tsx`, `access-subject-avatar.tsx` — chuyển nguyên.
- `src/modules/hr/hooks/use-access-subject-options.ts` — dựng `SubjectOption[]` từ 4 hook (hr sở hữu dữ liệu; `system` và `document` vốn đã import hook của hr — tiền lệ `role-permission-page.tsx`).
- `modules/document/types/document-access.ts` — `export { SUBJECT_KIND, … } from '@/shared/access-subject/subject-kind'` để 13 tệp cũ khỏi phải đổi (không phải barrel module; ghi chú lý do).
- Document: `folder-share-invite-form.tsx` (và nơi dùng picker/chips/avatar) đổi import + truyền `options` từ `useAccessSubjectOptions()`. Xóa 3 tệp cũ.
- Chuyển 2 tệp test picker sang `src/shared/access-subject/` (test thuần UI với options cố định — bỏ mock hook hr).

## Sở hữu tệp
Tạo: `src/shared/access-subject/*`, `src/modules/hr/hooks/use-access-subject-options.ts`. Sửa/xóa: các tệp trong `src/modules/document/components/` liệt kê ở Context + `document-access.ts`. KHÔNG chạm `modules/system`, `modules/report`.

## Các bước
1. Tạo `subject-kind.ts`, re-export ở `document-access.ts`.
2. Chuyển chips/avatar; đổi import.
3. Tách picker thuần UI + hook options ở hr; sửa `folder-share-invite-form.tsx`.
4. Chuyển test; `typecheck` + `lint` + `vitest run src/shared/access-subject src/modules/document`.

## Todo
- [x] hằng + kiểu sang shared
- [x] chips/avatar sang shared
- [x] picker thuần UI + `use-access-subject-options`
- [x] test chuyển + xanh

## Tiêu chí xong
Hộp «Chia sẻ» thư mục chạy y như cũ (kiểm tay: gõ không dấu, lọc loại, chọn nhiều). `grep -r "modules/" src/shared/access-subject` rỗng. 3 cổng xanh.

## Rủi ro
| Rủi ro | K×T | Giảm thiểu |
|---|---|---|
| Hồi quy hộp Chia sẻ văn bản | TB×TB | Test cũ chuyển theo, kiểm tay, phase tách riêng để revert độc lập |
| Phình phạm vi | Thấp×Thấp | Không đổi hành vi, chỉ đổi chỗ + tiêm options |
