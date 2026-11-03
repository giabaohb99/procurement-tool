# Phase 04 — nâng ô chọn chủ thể lên `src/shared/access-subject/`

## Trạng thái: DONE

## API mới cho phase 06 dùng

### `src/shared/access-subject/subject-kind.ts`
- `SUBJECT_KIND` (`employee:1, department:2, company:3, role:4`), `SUBJECT_KIND_LABELS`, `EFFECT` (`allow:1, deny:2`), `EFFECT_LABELS`, type `SubjectKind`.
- `interface MixedSubject { subject_kind: number; subject_id: number }` — value của picker.
- `interface SubjectOption { subject_kind: number; subject_id: number; label: string }` — dòng danh mục, nơi sở hữu dữ liệu tự dựng.

### `src/shared/access-subject/access-subject-picker.tsx`
```tsx
import { AccessSubjectPicker } from '@/shared/access-subject/access-subject-picker'
import type { MixedSubject } from '@/shared/access-subject/subject-kind'

<AccessSubjectPicker
  value={subjects}        // MixedSubject[]
  onChange={setSubjects}  // (v: MixedSubject[]) => void
  options={options}       // SubjectOption[] — tự dựng, picker KHÔNG gọi hook
  loading={loading}       // optional — đổi câu "Không có ai khớp." thành "Đang tải…"
/>
```
Thuần UI, không gọi `hr`. Hành vi giữ y bản cũ (gõ không dấu, nút lọc loại + đếm theo từ khóa, chọn nhiều, chip xóa từng cái, chặn lồng `<button>`).

### `src/shared/access-subject/access-subject-chips.tsx` → `SubjectChips`, `access-subject-avatar.tsx` → `AccessSubjectAvatar`
Chuyển nguyên, không đổi props/behavior.

### `src/modules/hr/hooks/use-access-subject-options.ts`
```ts
import { useAccessSubjectOptions } from '@/modules/hr/hooks/use-access-subject-options'
const { options, loading } = useAccessSubjectOptions()   // SubjectOption[], boolean
```
Gọi `useEmployees/useDepartments/useCompanies/useRoles` của `hr`, giữ đúng 2 quy tắc cũ: pháp nhân·phòng ban·vai trò lên trước người; tên phòng ban kèm tên pháp nhân (phòng trùng tên). `system` (phase 06) mượn hook này theo tiền lệ `role-permission-page.tsx`.

## Tệp

Tạo: `shared/access-subject/{subject-kind.ts, access-subject-picker.tsx, access-subject-picker-options.ts, access-subject-chips.tsx, access-subject-avatar.tsx, access-subject-picker.test.tsx}`, `modules/hr/hooks/use-access-subject-options.ts` + `.test.ts`.
Sửa: `modules/document/types/document-access.ts` (SUBJECT_KIND/EFFECT nay re-export từ shared, không phải barrel — ghi chú lý do tại chỗ), `folder-share-invite-form.tsx` (dùng picker+hook mới), 5 tệp còn import `SubjectChips`/`AccessSubjectAvatar` đổi đường dẫn (`document-access-fields.tsx`, `document-access-group-dialog.tsx`, `document-access-dialog.tsx`, `folder-share-people-list.tsx`, `document-share-access-list.tsx`).
Xóa: `folder-share-subject-picker.tsx`, `access-subject-chips.tsx`, `access-subject-avatar.tsx` (bản cũ trong `document/components/`) + 2 tệp test picker cũ (chuyển logic sang 2 tệp test mới: UI thuần ở shared, business rule ở hr hook).

13 tệp cũ `import … from '../types/document-access'` của `document/` **không đổi gì** (re-export giữ nguyên tên).

## Test
- `shared/access-subject/access-subject-picker.test.tsx` — 10 bài, options cố định, không mock hook hr (gộp cả 2 tệp test picker cũ + thêm case `loading`).
- `modules/hr/hooks/use-access-subject-options.test.ts` — 6 bài, mock 4 hook hr, giữ 3 business-rule cũ (thứ tự, phòng trùng tên, phòng đã giải thể bị loại) + case công ty không có `short_name` + 2 case `loading`.
- `folder-share-dialog.test.tsx` (đã có, không sửa) vẫn mock thẳng 4 hook hr — chạy xuyên qua `useAccessSubjectOptions` không cần đổi gì, vẫn xanh.

## Cổng
- `typecheck`: 0 lỗi.
- `lint`: 0 lỗi, 29 cảnh báo — toàn bộ nằm NGOÀI tệp vừa sửa (so khớp từng dòng cảnh báo), không thêm mới.
- `vitest run src/shared/access-subject src/modules/document src/modules/hr/hooks/use-access-subject-options.test.ts`: 92 tệp / 731 bài xanh.
- `grep -r "modules/" src/shared/access-subject` rỗng (đã sửa vài câu chú thích để literal-match, không chỉ ý nghĩa).

## Ghi chú không thuộc phần việc của tôi
`src/shared/constants/statuses.ts`, `modules/approval/components/approval-node-form.tsx`, `modules/approval/types/approval.ts`, `modules/hr/components/employee-tab-general.tsx` đang có thay đổi trong working tree — không phải tôi sửa (không nằm trong "File Ownership" của phase 04, không Edit/Write tới). Khả năng cao là agent BACKEND song song (`gen_status_ts.py` sinh `statuses.ts`) hoặc việc dở từ trước phiên này.

## Không có câu hỏi treo.
