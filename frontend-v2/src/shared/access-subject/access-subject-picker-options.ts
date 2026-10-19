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

/**
 * Gắn `key` + `kindLabel` lên từng dòng — `AccessSubjectPicker` chỉ lọc/tick trên dạng này.
 *
 * `labels` mặc định là bốn loại chung; nơi có thêm loại riêng (Kho skill AI có chức vụ, cấp bậc) truyền bảng nhãn
 * của mình vào — KHÔNG nhét thêm loại vào `SUBJECT_KIND_LABELS` chung, vì hộp quyền văn bản lặp qua bảng đó để bày ô
 * chọn loại và sẽ mọc ra hai loại văn bản không hỗ trợ.
 */
export function toPickerOptions(
  options: SubjectOption[],
  labels: Record<number, string> = SUBJECT_KIND_LABELS,
): SubjectPickerOption[] {
  return options.map((option) => ({
    ...option,
    key: keyOfSubject(option),
    kindLabel: labels[option.subject_kind] ?? '',
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
