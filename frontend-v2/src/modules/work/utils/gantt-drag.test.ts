import { describe, expect, it } from 'vitest'

import type { WorkTask } from '../types/work'
import { WORK_TASK_KIND, WORK_TASK_STATUS } from '../types/work'
import { datesToSave, edgeShift, readDragData, shiftedRange } from './gantt-drag'

/**
 * Luật kéo thanh Gantt. Sai ở đây là GHI ĐÈ ngày của việc thật bằng một ngày
 * người dùng chưa từng nhập — và họ không có cách nào biết ngày cũ là gì. Nên
 * phần lớn bài dưới đây kiểm chuyện KHÔNG lưu, chứ không phải chuyện lưu.
 */

function task(patch: Partial<WorkTask> = {}): WorkTask {
  return {
    id: 7, list_id: 1, section_id: 1, parent_id: null,
    title: 'Việc', description: '',
    status: WORK_TASK_STATUS.OPEN, kind: WORK_TASK_KIND.TASK,
    start_date: '', due_date: '', sort_order: 0,
    creator_employee_id: 0, completed_at: null, completed_by: null,
    created_at: '2026-08-01T00:00:00', updated_at: '2026-08-01T00:00:00',
    assignees: [], labels: [],
    subtask_done: 0, subtask_total: 0, comment_count: 0,
    ...patch,
  }
}

describe('edgeShift', () => {
  it('moves only the edge being dragged', () => {
    expect(edgeShift('move', 3)).toEqual({ start: 3, due: 3 })
    expect(edgeShift('start', 3)).toEqual({ start: 3, due: 0 })
    expect(edgeShift('end', 3)).toEqual({ start: 0, due: 3 })
  })
})

describe('readDragData', () => {
  it('rejects anything that is not a real drag payload', () => {
    //  `active.data.current` của dnd-kit là kiểu mở — đọc bừa là nổ runtime.
    expect(readDragData(undefined)).toBeNull()
    expect(readDragData(null)).toBeNull()
    expect(readDragData('move')).toBeNull()
    expect(readDragData({})).toBeNull()
    expect(readDragData({ task: task() })).toBeNull()
    expect(readDragData({ kind: 'move' })).toBeNull()
    expect(readDragData({ task: task(), kind: 'resize' })).toBeNull()
  })

  it('accepts the three known drag kinds', () => {
    expect(readDragData({ task: task(), kind: 'move' })?.kind).toBe('move')
    expect(readDragData({ task: task(), kind: 'start' })?.kind).toBe('start')
    expect(readDragData({ task: task(), kind: 'end' })?.kind).toBe('end')
  })
})

describe('shiftedRange', () => {
  it('returns null when the task has no date at all — nothing to shift', () => {
    expect(shiftedRange(task(), 'move', 5)).toBeNull()
  })

  it('treats a due-only task as a one-day bar so it can still be dragged', () => {
    expect(shiftedRange(task({ due_date: '2026-08-28' }), 'move', 2)).toEqual({
      start: '2026-08-30',
      due: '2026-08-30',
    })
  })

  it('shifts across a month boundary without drifting a day', () => {
    expect(shiftedRange(task({ start_date: '2026-08-30', due_date: '2026-08-31' }), 'move', 2))
      .toEqual({ start: '2026-09-01', due: '2026-09-02' })
  })
})

describe('datesToSave', () => {
  it('saves nothing when the bar snapped back to where it started', () => {
    expect(datesToSave(task({ due_date: '2026-08-28' }), 'move', 0)).toBeNull()
  })

  it('does NOT invent a start date when moving a due-only task', () => {
    //  Lỗi của bản đầu: kéo cả thanh là tự điền `start_date`, mở panel ra người
    //  dùng thấy một ngày lạ không biết ở đâu ra.
    expect(datesToSave(task({ due_date: '2026-08-28' }), 'move', 3)).toEqual({
      due_date: '2026-08-31',
    })
  })

  it('does NOT invent a due date when moving a start-only task', () => {
    expect(datesToSave(task({ start_date: '2026-08-28' }), 'move', -3)).toEqual({
      start_date: '2026-08-25',
    })
  })

  it('moves both ends when the task really has both', () => {
    expect(
      datesToSave(task({ start_date: '2026-08-20', due_date: '2026-08-28' }), 'move', 1),
    ).toEqual({ start_date: '2026-08-21', due_date: '2026-08-29' })
  })

  it('adds a start date when the left edge itself is dragged', () => {
    //  Đầu kia (`due_date`) đã có sẵn nên không phải ghi lại.
    expect(datesToSave(task({ due_date: '2026-08-28' }), 'start', -4)).toEqual({
      start_date: '2026-08-24',
    })
  })

  it('adds a due date when the right edge itself is dragged', () => {
    expect(datesToSave(task({ start_date: '2026-08-28' }), 'end', 4)).toEqual({
      due_date: '2026-09-01',
    })
  })

  it('kéo mép PHẢI của việc chỉ có hạn thì ghi luôn ngày bắt đầu — không thì quãng không lưu được', () => {
    //  Lỗi khách báo 31/08/2026: *"kéo dài ra thì nó chạy theo 1 ngày, ko ra
    //  duration"*. Chỉ ghi `due_date` thì `start_date` vẫn rỗng, mà
    //  `barGeometry` lấy `start_date || due_date` — thanh vẫn dài đúng một ngày
    //  và chỉ dịch đi, dù lớp phủ lúc kéo đã vẽ nó dài ra.
    //
    //  `start_date` lấy đúng ngày CŨ (28/08) nên không bịa gì: nó là ngày người
    //  dùng đã nhập, chỉ được ghi sang trường còn trống.
    expect(datesToSave(task({ due_date: '2026-08-28' }), 'end', 3)).toEqual({
      start_date: '2026-08-28',
      due_date: '2026-08-31',
    })
  })

  it('kéo mép TRÁI của việc chỉ có ngày bắt đầu thì ghi luôn hạn — cùng lý do', () => {
    expect(datesToSave(task({ start_date: '2026-08-28' }), 'start', -3)).toEqual({
      start_date: '2026-08-25',
      due_date: '2026-08-28',
    })
  })

  it('refuses to store an inverted range when an edge is dragged past the other', () => {
    //  Kéo mép trái vượt qua hạn: thà bỏ cả cú kéo còn hơn lưu ngày ngược rồi
    //  để báo cáo tính ra số ngày âm.
    expect(datesToSave(task({ start_date: '2026-08-20', due_date: '2026-08-28' }), 'start', 20))
      .toBeNull()
    expect(datesToSave(task({ start_date: '2026-08-20', due_date: '2026-08-28' }), 'end', -20))
      .toBeNull()
  })

  it('allows an edge dragged exactly onto the other — a one-day task is legal', () => {
    expect(datesToSave(task({ start_date: '2026-08-20', due_date: '2026-08-28' }), 'start', 8))
      .toEqual({ start_date: '2026-08-28' })
  })

  it('saves nothing for a task without dates, however far it is dragged', () => {
    expect(datesToSave(task(), 'move', 99)).toBeNull()
    expect(datesToSave(task(), 'start', -99)).toBeNull()
  })

  it('survives an absurd drag distance — years out, still a valid date', () => {
    expect(datesToSave(task({ due_date: '2026-08-28' }), 'move', 4000)).toEqual({
      due_date: '2037-08-10',
    })
  })
})
