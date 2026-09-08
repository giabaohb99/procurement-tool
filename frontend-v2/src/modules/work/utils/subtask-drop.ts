import type { WorkTask } from '../types/work'
import { SORT_STEP, resolveReorder } from './kanban-drop'

/**
 * Dữ liệu dnd-kit gắn vào một dòng VIỆC CON.
 *
 * Việc con không nằm trong payload bảng (C-05) — nó được nạp lười theo từng
 * việc cha đang bung — nên `TaskListView`, nơi bắt `onDragEnd`, không có cách
 * nào tra ra cha lẫn danh sách anh em của nó. Vì thế cả hai đi THEO món đồ đang
 * kéo thay vì tra ngược từ một bản đồ ở trên.
 */
export interface SubtaskDragData {
  type: 'subtask'
  taskId: number
  parentId: number
  /** Anh em cùng cha, đúng thứ tự đang hiển thị. */
  siblingIds: number[]
}

export function isSubtaskDragData(value: unknown): value is SubtaskDragData {
  if (!value || typeof value !== 'object') return false
  const data = value as Record<string, unknown>
  return (
    data.type === 'subtask' &&
    typeof data.taskId === 'number' &&
    typeof data.parentId === 'number' &&
    Array.isArray(data.siblingIds)
  )
}

/**
 * Chỗ việc con sẽ rơi vào sau một cú kéo; `null` = không làm gì.
 *
 * Trả `null` ở ba trường hợp, cả ba đều CỐ Ý im lặng:
 *
 * 1. Thả ra ngoài, hoặc thả lên một dòng không phải việc con (dòng cha, tiêu đề
 *    nhóm, «Việc mới»).
 * 2. Thả sang cụm của một việc cha KHÁC. Đó là phép đổi cha, mà `move_task` chỉ
 *    xếp lại thứ tự chứ không đụng `parent_id` — gửi đi là chắc chắn ăn 400.
 * 3. Thả về đúng chỗ cũ. Đừng bắn một lượt PATCH không đổi gì, nó chỉ làm bẩn
 *    nhật ký thao tác.
 */
export function resolveSubtaskDrop(
  active: SubtaskDragData,
  over: unknown,
): { parentId: number; beforeTaskId: number | null } | null {
  if (!isSubtaskDragData(over) || over.parentId !== active.parentId) return null

  const moved = resolveReorder(active.siblingIds, active.taskId, over.taskId)
  if (!moved) return null

  const at = active.siblingIds.indexOf(active.taskId)
  const rest = active.siblingIds.filter((id) => id !== active.taskId)
  if (moved.beforeId === (rest[at] ?? null)) return null

  return { parentId: active.parentId, beforeTaskId: moved.beforeId }
}

/**
 * Cụm việc con SAU cú thả — dùng cho cập nhật lạc quan.
 *
 * Đánh số `sort_order` lại y hệt máy chủ (`task_service.move_task`) để cái người
 * dùng thấy ngay và cái refetch trả về là một; lệch nhau thì dòng nhấp nháy nhảy
 * chỗ sau mỗi cú kéo.
 */
export function applyReorder(
  subtasks: WorkTask[],
  movedId: number,
  beforeId: number | null,
): WorkTask[] {
  const moved = subtasks.find((s) => s.id === movedId)
  if (!moved) return subtasks

  const rest = subtasks.filter((s) => s.id !== movedId)
  //  Mốc lạ (việc con vừa bị người khác xóa) thì xuống cuối — đúng như máy chủ.
  const found = beforeId === null ? -1 : rest.findIndex((s) => s.id === beforeId)
  rest.splice(found === -1 ? rest.length : found, 0, moved)

  return rest.map((s, i) => ({ ...s, sort_order: (i + 1) * SORT_STEP }))
}
