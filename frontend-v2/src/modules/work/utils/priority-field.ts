import type { WorkLabelField, WorkLabelOption, WorkTask } from '../types/work'

/**
 * ĐỘ ƯU TIÊN là một TRƯỜNG TÙY BIẾN nạp sẵn cho mỗi dự án, không còn là cột
 * cứng của task (migration `b2f7c1d94a30`).
 *
 * Vài chỗ vẫn cần biết "trường nào là độ ưu tiên" — tô màu thanh Gantt chẳng
 * hạn. Chúng tìm theo `system_key`, KHÔNG theo tên: tên là thứ người dùng đổi
 * được ngay trong menu «Tùy chỉnh», dò theo tên thì đổi tên xong màu biến mất.
 */
export const PRIORITY_SYSTEM_KEY = 'priority'

export function findPriorityField(fields: WorkLabelField[]): WorkLabelField | undefined {
  return fields.find((f) => f.system_key === PRIORITY_SYSTEM_KEY)
}

/** Giá trị ưu tiên của một việc, hoặc `undefined` khi chưa đặt / đã xóa trường. */
export function priorityOptionOf(
  task: WorkTask,
  field: WorkLabelField | undefined,
): WorkLabelOption | undefined {
  if (!field) return undefined
  const value = task.labels.find((l) => l.field_id === field.id)
  if (!value?.option_id) return undefined
  return field.options.find((o) => o.id === value.option_id)
}

/** Màu của bậc ưu tiên; chưa đặt thì xám — dùng cho thanh Gantt. */
export function priorityColorOf(task: WorkTask, field: WorkLabelField | undefined): string {
  return priorityOptionOf(task, field)?.color || 'slate'
}

/**
 * Hạng của từng giá trị để SẮP XẾP: `option_id` → thứ tự trong bộ giá trị.
 *
 * Sắp theo id giá trị là vô nghĩa (id sinh theo lúc tạo), còn theo tên thì "P10"
 * đứng trước "P2". Thứ tự do người dùng xếp trong bộ giá trị mới là thứ tự đúng.
 */
export function buildOptionRank(fields: WorkLabelField[]): Map<number, number> {
  const rank = new Map<number, number>()
  for (const field of fields) {
    field.options.forEach((option, i) => rank.set(option.id, i))
  }
  return rank
}
