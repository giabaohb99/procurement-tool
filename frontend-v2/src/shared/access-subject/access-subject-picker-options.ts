import { stripDiacritics } from '@/shared/utils/vn-text'
import { SUBJECT_KIND, SUBJECT_KIND_LABELS } from './subject-kind'
import type { MixedSubject, SubjectOption } from './subject-kind'

/** Một dòng danh mục đã gắn khóa lọc (`key`) và nhãn loại để hiện ra. */
export interface SubjectPickerOption extends SubjectOption {
  key: string
  kindLabel: string
}

/** Thứ tự nút lọc — cùng thứ tự xếp danh sách (pháp nhân/phòng ban/vai trò trước, người sau). */
export const KIND_FILTER_ORDER = [
  SUBJECT_KIND.company,
  SUBJECT_KIND.department,
  SUBJECT_KIND.role,
  SUBJECT_KIND.employee,
] as const

export function keyOfSubject(subject: MixedSubject): string {
  return `${subject.subject_kind}-${subject.subject_id}`
}

/** Gắn `key` + `kindLabel` lên từng dòng — `AccessSubjectPicker` chỉ lọc/tick trên dạng này. */
export function toPickerOptions(options: SubjectOption[]): SubjectPickerOption[] {
  return options.map((option) => ({
    ...option,
    key: keyOfSubject(option),
    kindLabel: SUBJECT_KIND_LABELS[option.subject_kind],
  }))
}

/** Lọc không phân biệt dấu — gõ "ke toan" vẫn khớp "Kế toán". */
export function filterOptionsByKeyword(
  options: SubjectPickerOption[],
  keyword: string,
): SubjectPickerOption[] {
  const needle = stripDiacritics(keyword.trim().toLowerCase())
  if (!needle) return options
  return options.filter((option) => stripDiacritics(option.label.toLowerCase()).includes(needle))
}
