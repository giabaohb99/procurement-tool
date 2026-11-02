import { FORUM_PREFIX } from '@/shared/constants/statuses'
import type { StatusOption } from '@/shared/constants/statuses'

/** Giá trị nhãn "Thông báo" trong bộ mã `forum_prefix` (bao-CR-707) — khớp `ForumPrefix.ANNOUNCEMENT`. */
export const ANNOUNCEMENT_PREFIX = 6

/**
 * Các lựa chọn nhãn cho ô chọn ở hộp đăng/sửa bài. Nhãn Thông báo chỉ quản trị
 * diễn đàn gắn được (backend chặn 403) — người thường không thấy nó trong danh sách,
 * trừ khi bài đang mang sẵn nhãn đó (sửa bài người khác đã gắn) để ô chọn còn hiện đúng giá trị.
 */
export function listPrefixOptions(canAnnounce: boolean, current = 0): readonly StatusOption[] {
  if (canAnnounce || current === ANNOUNCEMENT_PREFIX) return FORUM_PREFIX
  return FORUM_PREFIX.filter((option) => Number(option.value) !== ANNOUNCEMENT_PREFIX)
}
