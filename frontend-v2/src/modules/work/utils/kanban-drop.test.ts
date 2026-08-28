import { arrayMove } from '@dnd-kit/sortable'
import { describe, expect, it } from 'vitest'

import type { WorkTask } from '../types/work'
import {
  SORT_STEP,
  applyMove,
  columnDroppableId,
  groupBySection,
  isSamePlace,
  parseDropTarget,
  resolveDropPlace,
  taskDraggableId,
} from './kanban-drop'

/**
 * Kéo thả kanban. Ba lỗi tệp này canh, đừng gỡ test nào:
 *
 * 1. **Kéo XUỐNG trong cùng một cột lệch một chỗ** — dnd-kit vẽ trước theo
 *    `arrayMove` (thẻ nằm SAU ô đích) còn lúc thả lại chèn TRƯỚC ô đích.
 * 2. **Không thả được vào cột RỖNG** — `over` là chính cột chứ không phải thẻ.
 * 3. **Đánh số lạc quan phải trùng máy chủ** — lệch thì thẻ nhảy chỗ khi refetch.
 */

function task(id: number, sectionId: number | null, sortOrder: number): WorkTask {
  return {
    id,
    list_id: 1,
    section_id: sectionId,
    parent_id: null,
    title: `Việc ${id}`,
    description: '',
    status: 1,
    priority: 0,
    start_date: '',
    due_date: '',
    sort_order: sortOrder,
    creator_employee_id: 11,
    completed_at: null,
    completed_by: null,
    created_at: '2026-08-01T00:00:00',
    updated_at: '2026-08-01T00:00:00',
    assignees: [],
    tag_ids: [],
    labels: [],
    subtask_done: 0,
    subtask_total: 0,
    comment_count: 0,
  }
}

/** Cột `sectionId` với các thẻ mang đúng những id đó, giãn đều. */
function column(sectionId: number, ids: number[]): WorkTask[] {
  return ids.map((id, i) => task(id, sectionId, (i + 1) * SORT_STEP))
}

const ids = (ds: WorkTask[] | undefined) => (ds ?? []).map((t) => t.id)

/** Thứ tự cột `sectionId` đọc lại từ một mảng task phẳng, đúng luật máy chủ. */
function orderOf(tasks: WorkTask[], sectionId: number): number[] {
  return ids(groupBySection([sectionId], tasks).get(sectionId))
}

// ── Đọc id vùng thả ────────────────────────────────────────────────────────────

describe('parseDropTarget', () => {
  it('reads back exactly what the id helpers produce', () => {
    expect(parseDropTarget(columnDroppableId(7))).toEqual({ type: 'section', sectionId: 7 })
    expect(parseDropTarget(taskDraggableId(42))).toEqual({ type: 'task', taskId: 42 })
  })

  it.each([
    undefined,
    null,
    '',
    'section-',
    'task-',
    'section-0',
    'task-0',
    'section--1',
    'task-1.5',
    'task- 12',
    'task-12 ',
    'section-abc',
    // `Number('1e3')` = 1000: khớp lỏng bằng Number thì id này thành thẻ #1000
    // của người khác. Chính là lý do dùng biểu thức chính quy.
    'task-1e3',
    'task-0x0c',
    'task-Infinity',
    'work-task-3',
    'section-1-extra',
    12,
  ])('rejects the junk id %p instead of guessing a number', (raw) => {
    expect(parseDropTarget(raw)).toBeNull()
  })
})

// ── Gom theo cột ───────────────────────────────────────────────────────────────

describe('groupBySection', () => {
  it('breaks sort_order ties by id, exactly like the server ORDER BY', () => {
    //  Dữ liệu cũ để `sort_order = 0` cho cả cột. Sắp thiếu vế `id` thì thứ tự
    //  lạc quan khác thứ tự refetch và thẻ tự nhảy chỗ sau khi buông tay.
    const tasks = [task(9, 1, 0), task(3, 1, 0), task(7, 1, 0)]
    expect(orderOf(tasks, 1)).toEqual([3, 7, 9])
  })

  it('keeps declared empty columns and drops tasks with no column', () => {
    const map = groupBySection([1, 2], [task(1, null, 0), task(2, 99, 0), task(3, 2, 10)])
    expect(ids(map.get(1))).toEqual([])
    expect(ids(map.get(2))).toEqual([3])
    expect(map.has(99)).toBe(false)
  })

  it('survives an empty board and an empty section list', () => {
    expect(groupBySection([], []).size).toBe(0)
    expect(ids(groupBySection([1], []).get(1))).toEqual([])
  })
})

// ── Cùng một cột: phải khớp arrayMove của dnd-kit ──────────────────────────────

describe('resolveDropPlace — trong cùng một cột', () => {
  const COLUMN = column(1, [10, 20, 30, 40, 50])
  const cols = new Map([[1, COLUMN]])

  it('matches dnd-kit arrayMove for every from/to pair, in both directions', () => {
    //  Lỗi gốc: chèn TRƯỚC ô đích cho mọi trường hợp, nên mọi cú kéo XUỐNG rơi
    //  lệch một chỗ so với hình dnd-kit vừa vẽ. Quét hết cặp thay vì chọn vài ca.
    const origIds = COLUMN.map((t) => t.id)
    for (let from = 0; from < origIds.length; from += 1) {
      for (let to = 0; to < origIds.length; to += 1) {
        const place = resolveDropPlace(cols, origIds[from], { type: 'task', taskId: origIds[to] })
        expect(place).not.toBeNull()
        const after = applyMove(COLUMN, origIds[from], place!)
        expect(orderOf(after, 1)).toEqual(arrayMove(origIds, from, to))
      }
    }
  })

  it('drops onto the column background = move to the very end', () => {
    const place = resolveDropPlace(cols, 10, { type: 'section', sectionId: 1 })
    expect(place).toEqual({ sectionId: 1, beforeTaskId: null })
    expect(orderOf(applyMove(COLUMN, 10, place!), 1)).toEqual([20, 30, 40, 50, 10])
  })

  it('hovering the dragged card itself keeps it exactly where it is', () => {
    //  dnd-kit bắn `over = chính nó` liên tục trong lúc rê. Thiếu nhánh này thì
    //  mỗi nhịp chuột là một lệnh "xuống cuối cột".
    for (const id of [10, 30, 50]) {
      const place = resolveDropPlace(cols, id, { type: 'task', taskId: id })
      expect(orderOf(applyMove(COLUMN, id, place!), 1)).toEqual([10, 20, 30, 40, 50])
      expect(isSamePlace(cols, COLUMN.find((t) => t.id === id)!, place!)).toBe(true)
    }
  })

  it('handles a one-card column without inventing a neighbour', () => {
    const single = column(1, [10])
    const oneCol = new Map([[1, single]])
    expect(resolveDropPlace(oneCol, 10, { type: 'task', taskId: 10 })).toEqual({
      sectionId: 1,
      beforeTaskId: null,
    })
    expect(resolveDropPlace(oneCol, 10, { type: 'section', sectionId: 1 })).toEqual({
      sectionId: 1,
      beforeTaskId: null,
    })
  })

  it('moves the head of a 1000-card column to the tail without losing anyone', () => {
    const bigColumn = column(1, Array.from({ length: 1000 }, (_, i) => i + 1))
    const cols = new Map([[1, bigColumn]])
    const place = resolveDropPlace(cols, 1, { type: 'task', taskId: 1000 })
    const after = applyMove(bigColumn, 1, place!)
    const order = orderOf(after, 1)
    expect(order).toHaveLength(1000)
    expect(order[999]).toBe(1)
    expect(order[0]).toBe(2)
    expect(new Set(order).size).toBe(1000)
  })
})

// ── Sang cột khác ──────────────────────────────────────────────────────────────

describe('resolveDropPlace — sang cột khác', () => {
  const A = column(1, [10, 20])
  const B = column(2, [30, 40])
  const cols = new Map([
    [1, A],
    [2, B],
    [3, []],
  ])
  const all = [...A, ...B]

  it('drops into an EMPTY column — the bug that made column «Đã xong» refuse cards', () => {
    const place = resolveDropPlace(cols, 10, { type: 'section', sectionId: 3 })
    expect(place).toEqual({ sectionId: 3, beforeTaskId: null })

    const after = applyMove(all, 10, place!)
    expect(orderOf(after, 3)).toEqual([10])
    expect(orderOf(after, 1)).toEqual([20])
    expect(after.find((t) => t.id === 10)?.section_id).toBe(3)
    expect(after.find((t) => t.id === 10)?.sort_order).toBe(SORT_STEP)
  })

  it('inserts before the hovered card — same index the placeholder is drawn at', () => {
    const place = resolveDropPlace(cols, 10, { type: 'task', taskId: 40 })
    expect(place).toEqual({ sectionId: 2, beforeTaskId: 40 })
    expect(orderOf(applyMove(all, 10, place!), 2)).toEqual([30, 10, 40])
  })

  it('inserts at the head when hovering the first card of the other column', () => {
    const place = resolveDropPlace(cols, 20, { type: 'task', taskId: 30 })
    expect(orderOf(applyMove(all, 20, place!), 2)).toEqual([20, 30, 40])
  })

  it('drops on the other column background = append at the end', () => {
    const place = resolveDropPlace(cols, 10, { type: 'section', sectionId: 2 })
    expect(orderOf(applyMove(all, 10, place!), 2)).toEqual([30, 40, 10])
  })

  it('leaves the source column renumbered-free and closed up', () => {
    const place = resolveDropPlace(cols, 10, { type: 'task', taskId: 30 })
    const after = applyMove(all, 10, place!)
    expect(orderOf(after, 1)).toEqual([20])
    expect(after.find((t) => t.id === 20)?.sort_order).toBe(2 * SORT_STEP)
  })
})

// ── Vòng XEM TRƯỚC lúc kéo qua cột khác ───────────────────────────────────────

describe('vòng xem trước — thẻ được dời sang cột đích ngay trong lúc kéo', () => {
  //  `kanban-board.tsx` dời hẳn thẻ sang cột đích khi kéo qua (để cột đó dùng
  //  đúng hiệu ứng sortable của nó), rồi các nhịp sau lại tính đích trên chính
  //  ảnh vừa vẽ. Vòng lặp đó phải ĐỨNG YÊN — không thì cột rung liên tục.
  const SECTIONS = [1, 2]
  const origIds = [...column(1, [10, 20]), ...column(2, [30, 40])]

  function preview(tasks: WorkTask[], activeId: number, targetId: string) {
    const cols = groupBySection(SECTIONS, tasks)
    const place = resolveDropPlace(cols, activeId, parseDropTarget(targetId))
    return { place, cols, after: place ? applyMove(tasks, activeId, place) : tasks }
  }

  it('settles after one hop — hovering the card again resolves to the same spot', () => {
    const hop1 = preview(origIds, 10, taskDraggableId(40))
    expect(orderOf(hop1.after, 2)).toEqual([30, 10, 40])

    //  Nhịp kế: con trỏ vẫn trên thẻ đang kéo, giờ đã nằm trong cột đích.
    const hop2 = preview(hop1.after, 10, taskDraggableId(10))
    expect(hop2.place).toEqual(hop1.place)
    expect(orderOf(hop2.after, 2)).toEqual([30, 10, 40])
    expect(orderOf(hop2.after, 1)).toEqual([20])
  })

  it('is stable for an empty column too — no ping-pong back to the source', () => {
    const withEmpty = groupBySection([1, 2, 3], origIds)
    const p1 = resolveDropPlace(withEmpty, 10, { type: 'section', sectionId: 3 })
    const afterFirst = applyMove(origIds, 10, p1!)

    const p2 = resolveDropPlace(groupBySection([1, 2, 3], afterFirst), 10, {
      type: 'section',
      sectionId: 3,
    })
    expect(p2).toEqual({ sectionId: 3, beforeTaskId: null })
    expect(orderOf(applyMove(afterFirst, 10, p2!), 3)).toEqual([10])
  })

  it('lets the card come back to where it started, and knows that is a no-op', () => {
    const { after } = preview(origIds, 10, taskDraggableId(30))
    const back = preview(after, 10, taskDraggableId(20))
    expect(back.place).toEqual({ sectionId: 1, beforeTaskId: 20 })

    //  So với ảnh GỐC (thẻ 10 đứng đầu cột 1) thì đây đúng là chỗ cũ → không gọi API.
    const initial = groupBySection(SECTIONS, origIds)
    expect(isSamePlace(initial, origIds[0], back.place!)).toBe(true)
  })
})

// ── Đích rác / dữ liệu lệch ────────────────────────────────────────────────────

describe('resolveDropPlace — đích không dùng được', () => {
  const cols = new Map([
    [1, column(1, [10, 20])],
    [2, []],
  ])

  it('returns null instead of guessing when the target is junk or missing', () => {
    expect(resolveDropPlace(cols, 10, null)).toBeNull()
    expect(resolveDropPlace(cols, 10, parseDropTarget('rác'))).toBeNull()
  })

  it('returns null when the dragged card is not on the board at all', () => {
    expect(resolveDropPlace(cols, 999, { type: 'task', taskId: 10 })).toBeNull()
    expect(resolveDropPlace(cols, 999, { type: 'section', sectionId: 1 })).toBeNull()
  })

  it('returns null for a column that was deleted by someone else mid-drag', () => {
    expect(resolveDropPlace(cols, 10, { type: 'section', sectionId: 77 })).toBeNull()
    expect(resolveDropPlace(cols, 10, { type: 'task', taskId: 555 })).toBeNull()
  })

  it('returns null on an empty board', () => {
    expect(resolveDropPlace(new Map(), 10, { type: 'section', sectionId: 1 })).toBeNull()
  })
})

// ── Bỏ qua cú thả không đổi gì ─────────────────────────────────────────────────

describe('isSamePlace', () => {
  const COLUMN = column(1, [10, 20, 30])
  const cols = new Map([
    [1, COLUMN],
    [2, []],
  ])

  it('spots a no-op drop anywhere in the column, head to tail', () => {
    expect(isSamePlace(cols, COLUMN[0], { sectionId: 1, beforeTaskId: 20 })).toBe(true)
    expect(isSamePlace(cols, COLUMN[1], { sectionId: 1, beforeTaskId: 30 })).toBe(true)
    expect(isSamePlace(cols, COLUMN[2], { sectionId: 1, beforeTaskId: null })).toBe(true)
  })

  it('does not swallow a real move', () => {
    expect(isSamePlace(cols, COLUMN[0], { sectionId: 1, beforeTaskId: 30 })).toBe(false)
    expect(isSamePlace(cols, COLUMN[0], { sectionId: 1, beforeTaskId: null })).toBe(false)
    expect(isSamePlace(cols, COLUMN[0], { sectionId: 2, beforeTaskId: null })).toBe(false)
  })

  it('is false for a card that is not in the column any more', () => {
    expect(isSamePlace(cols, task(99, 1, 0), { sectionId: 1, beforeTaskId: null })).toBe(false)
  })
})

// ── Cập nhật lạc quan ──────────────────────────────────────────────────────────

describe('applyMove', () => {
  it('renumbers the whole target column with the server step, no ties left', () => {
    const tasks = [task(1, 1, 0), task(2, 1, 0), task(3, 1, 0)]   // cả cột trùng 0
    const after = applyMove(tasks, 3, { sectionId: 1, beforeTaskId: 1 })
    expect(orderOf(after, 1)).toEqual([3, 1, 2])
    expect(after.map((t) => t.sort_order).sort((a, b) => a - b)).toEqual([1000, 2000, 3000])
  })

  it('never touches subtasks or other columns', () => {
    const subtask = task(9, null, 0)
    subtask.parent_id = 1
    const otherSection = task(8, 2, 55)
    const after = applyMove([task(1, 1, 0), task(2, 1, 0), subtask, otherSection], 2, {
      sectionId: 1,
      beforeTaskId: 1,
    })
    expect(after.find((t) => t.id === 9)).toBe(subtask)
    expect(after.find((t) => t.id === 8)).toBe(otherSection)
  })

  it('appends when the anchor vanished (someone else moved that card first)', () => {
    const tasks = column(1, [10, 20, 30])
    expect(orderOf(applyMove(tasks, 10, { sectionId: 1, beforeTaskId: 999 }), 1)).toEqual([
      20, 30, 10,
    ])
  })

  it('is idempotent — re-applying a place that already holds changes nothing', () => {
    //  `kanban-board.tsx` GIỮ ảnh vừa thả thêm một nhịp sau khi buông tay, nên
    //  có đúng một lần vẽ mà `applyMove` chạy trên dữ liệu ĐÃ cập nhật với vẫn
    //  cái mốc cũ. Không bất biến thì thẻ bị dời thêm một nấc nữa.
    const origIds = [...column(1, [10, 20]), ...column(2, [30, 40])]
    const place = { sectionId: 2, beforeTaskId: 40 }
    const first = applyMove(origIds, 10, place)
    const second = applyMove(first, 10, place)
    expect(orderOf(second, 2)).toEqual(orderOf(first, 2))
    expect(orderOf(second, 1)).toEqual(orderOf(first, 1))
    expect(second.map((t) => [t.id, t.section_id, t.sort_order])).toEqual(
      first.map((t) => [t.id, t.section_id, t.sort_order]),
    )
  })

  it('is idempotent for the append-to-end anchor too', () => {
    const origIds = [...column(1, [10, 20]), ...column(2, [30])]
    const place = { sectionId: 2, beforeTaskId: null }
    const first = applyMove(origIds, 20, place)
    const second = applyMove(first, 20, place)
    expect(orderOf(second, 2)).toEqual([30, 20])
    expect(orderOf(first, 2)).toEqual([30, 20])
    expect(second.map((t) => t.sort_order)).toEqual(first.map((t) => t.sort_order))
  })

  it('returns the list untouched when the dragged card is unknown', () => {
    const tasks = column(1, [10, 20])
    expect(applyMove(tasks, 999, { sectionId: 1, beforeTaskId: null })).toBe(tasks)
  })

  it('does not mutate the input array or its items', () => {
    const tasks = column(1, [10, 20, 30])
    const anh = tasks.map((t) => ({ ...t }))
    applyMove(tasks, 30, { sectionId: 2, beforeTaskId: null })
    expect(tasks).toEqual(anh)
  })

  it('moving into a column that has no cards yet gives the first slot', () => {
    const after = applyMove([task(10, 1, SORT_STEP)], 10, { sectionId: 5, beforeTaskId: null })
    expect(after[0]).toMatchObject({ section_id: 5, sort_order: SORT_STEP })
  })
})
