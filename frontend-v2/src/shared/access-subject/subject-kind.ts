/**
 * BỐN LOẠI CHỦ THỂ dùng chung cho mọi màn gán quyền kiểu Drive — người ·
 * phòng ban · pháp nhân · vai trò, cùng chiều tác động «cho phép / cấm»
 * (`EFFECT`).
 *
 * Chuyển từ `document/types/document-access.ts` (phase 04, kế hoạch
 * `plans/261002-0836-phan-quyen-tung-bao-cao`) lên `shared/` vì không có gì
 * riêng cho văn bản — phân hệ Báo cáo (phase 06 của kế hoạch trên) gán quyền
 * theo đúng bốn chủ thể này, không nên bê nguyên một bộ hằng số thứ hai.
 * `document-access.ts` vẫn re-export từ đây để các tệp cũ của `document/`
 * khỏi phải đổi import.
 */

export const SUBJECT_KIND = {
  employee: 1,
  department: 2,
  company: 3,
  role: 4,
} as const

export type SubjectKind = (typeof SUBJECT_KIND)[keyof typeof SUBJECT_KIND]

export const SUBJECT_KIND_LABELS: Record<number, string> = {
  1: 'Người',
  2: 'Phòng ban',
  3: 'Pháp nhân',
  4: 'Vai trò',
}

export const EFFECT = { allow: 1, deny: 2 } as const

export type Effect = (typeof EFFECT)[keyof typeof EFFECT]

export const EFFECT_LABELS: Record<number, string> = {
  1: 'Cho phép',
  2: 'Không cho phép',
}

/** Một chủ thể ĐÃ CHỌN — chưa kèm tên, dùng làm `value` của `AccessSubjectPicker`. */
export interface MixedSubject {
  subject_kind: number
  subject_id: number
}

/**
 * Một dòng trong danh mục để CHỌN, đã kèm tên hiện ra.
 *
 * Nơi sở hữu dữ liệu (hr với người/phòng/pháp nhân/vai trò) dựng mảng này rồi
 * truyền vào `AccessSubjectPicker` qua prop `options` — `shared/` không tự gọi
 * API để giữ đúng luật "`shared/` không import các phân hệ".
 */
export interface SubjectOption {
  subject_kind: number
  subject_id: number
  label: string
}
