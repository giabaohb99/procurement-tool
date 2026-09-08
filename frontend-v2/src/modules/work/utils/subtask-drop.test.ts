import { describe, expect, it } from 'vitest'

import type { WorkTask } from '../types/work'
import { SORT_STEP } from './kanban-drop'
import {
  applyReorder,
  isSubtaskDragData,
  resolveSubtaskDrop,
  type SubtaskDragData,
} from './subtask-drop'

/** Cụm ba việc con cùng một cha, đúng thứ tự hiển thị. */
const SIBLINGS = [10, 11, 12]

function dragData(taskId: number, overrides: Partial<SubtaskDragData> = {}): SubtaskDragData {
  return { type: 'subtask', taskId, parentId: 5, siblingIds: SIBLINGS, ...overrides }
}

function subtask(id: number, sortOrder: number): WorkTask {
  return { id, title: `Việc con ${id}`, sort_order: sortOrder } as WorkTask
}

describe('isSubtaskDragData', () => {
  it('accepts a well-formed payload', () => {
    expect(isSubtaskDragData(dragData(10))).toBe(true)
  })

  it('rejects the payload of a parent task row', () => {
    expect(isSubtaskDragData({ type: 'task', taskId: 10, sectionId: 3 })).toBe(false)
  })

  it('rejects null, undefined and primitives instead of throwing', () => {
    //  `event.over` rỗng khi thả ra ngoài bảng — đi thẳng vào đây.
    expect(isSubtaskDragData(null)).toBe(false)
    expect(isSubtaskDragData(undefined)).toBe(false)
    expect(isSubtaskDragData('subtask')).toBe(false)
    expect(isSubtaskDragData(7)).toBe(false)
  })

  it('rejects a payload missing parentId or siblingIds', () => {
    expect(isSubtaskDragData({ type: 'subtask', taskId: 10, siblingIds: [] })).toBe(false)
    expect(isSubtaskDragData({ type: 'subtask', taskId: 10, parentId: 5 })).toBe(false)
  })
})

describe('resolveSubtaskDrop', () => {
  it('moves down: the dragged item lands AFTER the row it was dropped on', () => {
    //  10 thả lên 11 → hàng bỏ 10 ra là [11, 12], ô đích là chỉ số 1 → mốc là 12.
    expect(resolveSubtaskDrop(dragData(10), dragData(11))).toEqual({
      parentId: 5,
      beforeTaskId: 12,
    })
  })

  it('moves up: the dragged item lands BEFORE the row it was dropped on', () => {
    expect(resolveSubtaskDrop(dragData(12), dragData(10))).toEqual({
      parentId: 5,
      beforeTaskId: 10,
    })
  })

  it('drops to the end when the target is the last row', () => {
    expect(resolveSubtaskDrop(dragData(10), dragData(12))).toEqual({
      parentId: 5,
      beforeTaskId: null,
    })
  })

  it('does nothing when dropped back on itself', () => {
    //  Rê qua chính nó là chuyện xảy ra liên tục lúc kéo; bắn PATCH mỗi lần thì
    //  nhật ký thao tác đầy rác mà thứ tự không đổi.
    expect(resolveSubtaskDrop(dragData(11), dragData(11))).toBeNull()
  })

  it('refuses a drop into another parent cluster', () => {
    //  Đổi cha là phép khác hẳn, `move_task` không đụng `parent_id` — gửi đi là
    //  chắc chắn ăn 400.
    const other = dragData(20, { parentId: 9, siblingIds: [20, 21] })
    expect(resolveSubtaskDrop(dragData(10), other)).toBeNull()
  })

  it('refuses a drop on a parent row, a group or empty space', () => {
    expect(resolveSubtaskDrop(dragData(10), { type: 'task', taskId: 3, sectionId: 1 })).toBeNull()
    expect(resolveSubtaskDrop(dragData(10), { type: 'section', sectionId: 1 })).toBeNull()
    expect(resolveSubtaskDrop(dragData(10), undefined)).toBeNull()
  })

  it('refuses when the dragged id is not in its own sibling list', () => {
    //  Cụm vừa bị người khác sửa trong lúc tay đang giữ chuột.
    const stale = dragData(99)
    expect(resolveSubtaskDrop(stale, dragData(11))).toBeNull()
  })

  it('handles a cluster of one — every drop is a no-op', () => {
    const only = dragData(10, { siblingIds: [10] })
    expect(resolveSubtaskDrop(only, only)).toBeNull()
  })
})

describe('applyReorder', () => {
  const SUBS = [subtask(10, 1000), subtask(11, 2000), subtask(12, 3000)]

  it('renumbers every row by SORT_STEP, matching the server', () => {
    //  Lệch cách đánh số với máy chủ thì sau mỗi cú kéo dòng nhấp nháy nhảy chỗ
    //  một nhịp khi refetch về.
    const moved = applyReorder(SUBS, 12, 10)

    expect(moved.map((s) => s.id)).toEqual([12, 10, 11])
    expect(moved.map((s) => s.sort_order)).toEqual([SORT_STEP, 2 * SORT_STEP, 3 * SORT_STEP])
  })

  it('sends the row to the end when the marker is null', () => {
    expect(applyReorder(SUBS, 10, null).map((s) => s.id)).toEqual([11, 12, 10])
  })

  it('sends the row to the end when the marker no longer exists', () => {
    //  Việc con làm mốc vừa bị người khác xóa — lệch một chỗ còn hơn ném lên đầu.
    expect(applyReorder(SUBS, 10, 999).map((s) => s.id)).toEqual([11, 12, 10])
  })

  it('returns the list untouched when the moved row is unknown', () => {
    expect(applyReorder(SUBS, 999, 10)).toBe(SUBS)
  })

  it('does not mutate the input array', () => {
    const before = SUBS.map((s) => s.sort_order)
    applyReorder(SUBS, 12, 10)
    expect(SUBS.map((s) => s.sort_order)).toEqual(before)
  })

  it('survives an empty list', () => {
    expect(applyReorder([], 10, null)).toEqual([])
  })
})
