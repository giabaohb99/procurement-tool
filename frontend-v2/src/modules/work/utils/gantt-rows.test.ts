import { describe, expect, it } from 'vitest'

import type { WorkTask } from '../types/work'
import { WORK_TASK_KIND, WORK_TASK_STATUS } from '../types/work'
import { buildGanttRows, indexTaskRows, rollUpRange } from './gantt-rows'
import type { TaskGroup } from './group-tasks'

/**
 * Hàng của biểu đồ Gantt. Chỉ số của một hàng CHÍNH LÀ tọa độ dọc của nó — lưới
 * trái, các thanh và lớp mũi tên đều nhân chỉ số ấy với chiều cao hàng. Lệch một
 * hàng ở đây là mũi tên nối vào việc bên cạnh, mà nhìn thì vẫn "có vẻ đúng".
 */

function task(patch: Partial<WorkTask> = {}): WorkTask {
  return {
    id: 1, list_id: 1, section_id: 1, parent_id: null,
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

function group(key: string, tasks: WorkTask[]): TaskGroup {
  return { key, name: key, color: 'slate', sectionId: 1, tasks }
}

const isDone = (t: WorkTask) => t.status === WORK_TASK_STATUS.DONE
const moKhap = () => false

/** Bộ tùy chọn tối thiểu: mở hết nhóm, không bung việc con, không dòng nháp. */
function opts(patch: Partial<Parameters<typeof buildGanttRows>[1]> = {}) {
  return {
    isCollapsed: moKhap,
    isDone,
    expandedTaskId: null,
    subtasks: [],
    showDraftRow: false,
    ...patch,
  }
}

describe('buildGanttRows', () => {
  it('mỗi nhóm một dòng tiêu đề, việc của nó nằm ngay dưới', () => {
    const rows = buildGanttRows(
      [group('a', [task({ id: 1 }), task({ id: 2 })]), group('b', [task({ id: 3 })])],
      opts(),
    )
    expect(rows.map((r) => r.kind)).toEqual(['group', 'task', 'task', 'group', 'task'])
  })

  it('nhóm ĐANG THU thì giấu việc nhưng GIỮ dòng tiêu đề', () => {
    //  Giấu cả dòng tiêu đề thì không còn chỗ nào bấm để mở nhóm ra lại.
    const rows = buildGanttRows([group('a', [task({ id: 1 })])], opts({ isCollapsed: () => true }))
    expect(rows).toHaveLength(1)
    expect(rows[0].kind).toBe('group')
  })

  it('nhóm RỖNG vẫn có dòng, tiến độ 0 chứ không chia cho 0', () => {
    const rows = buildGanttRows([group('a', [])], opts())
    expect(rows).toHaveLength(1)
    expect(rows[0].kind === 'group' && rows[0].progress).toBe(0)
    expect(rows[0].kind === 'group' && rows[0].range).toBe(null)
  })

  it('tiến độ nhóm = số việc XONG trên tổng số việc', () => {
    const rows = buildGanttRows(
      [
        group('a', [
          task({ id: 1, status: WORK_TASK_STATUS.DONE }),
          task({ id: 2 }),
          task({ id: 3, status: WORK_TASK_STATUS.DONE }),
          task({ id: 4 }),
        ]),
      ],
      opts(),
    )
    expect(rows[0].kind === 'group' && rows[0].progress).toBe(0.5)
  })

  it('không nhóm nào thì không hàng nào — biểu đồ trống, không nổ', () => {
    expect(buildGanttRows([], opts())).toEqual([])
  })

  it('việc ĐANG BUNG kéo theo đúng số dòng việc con, ngay dưới nó', () => {
    //  Đây là chỗ hai bên dễ lệch nhất: lưới trái bung ba việc con mà trục thời
    //  gian chỉ chừa một hàng thì MỌI thanh bên dưới trượt khỏi tên việc của nó.
    const rows = buildGanttRows(
      [group('a', [task({ id: 1 }), task({ id: 2 })])],
      opts({
        expandedTaskId: 1,
        subtasks: [task({ id: 11 }), task({ id: 12 })],
      }),
    )
    expect(rows.map((r) => r.key)).toEqual(['g:a', 't:1', 's:11', 's:12', 't:2'])
    expect(rows.filter((r) => r.kind === 'task').map((r) => r.isSubtask)).toEqual([
      false,
      true,
      true,
      false,
    ])
  })

  it('việc con chỉ nở ra dưới ĐÚNG việc đang bung, không dưới việc khác', () => {
    const rows = buildGanttRows(
      [group('a', [task({ id: 1 })]), group('b', [task({ id: 2 })])],
      opts({ expandedTaskId: 2, subtasks: [task({ id: 21 })] }),
    )
    expect(rows.map((r) => r.key)).toEqual(['g:a', 't:1', 'g:b', 't:2', 's:21'])
  })

  it('đang bung mà việc con CHƯA về thì không chừa hàng ma', () => {
    //  Việc con nạp lười: giữa lúc chờ, `subtasks` rỗng. Chừa sẵn hàng cho nó là
    //  lệch hàng đúng trong khoảng thời gian chờ ấy.
    const rows = buildGanttRows(
      [group('a', [task({ id: 1 })])],
      opts({ expandedTaskId: 1, subtasks: [] }),
    )
    expect(rows.map((r) => r.key)).toEqual(['g:a', 't:1'])
  })

  it('dòng «Việc mới» nằm CUỐI mỗi nhóm, và chỉ khi đủ quyền sửa', () => {
    const groups = [group('a', [task({ id: 1 })]), group('b', [])]
    expect(buildGanttRows(groups, opts({ showDraftRow: true })).map((r) => r.key)).toEqual([
      'g:a',
      't:1',
      'd:a',
      'g:b',
      'd:b',
    ])
    expect(buildGanttRows(groups, opts()).map((r) => r.key)).toEqual(['g:a', 't:1', 'g:b'])
  })

  it('nhóm đang THU thì không có dòng «Việc mới» — nó nằm trong thân nhóm', () => {
    const rows = buildGanttRows(
      [group('a', [task({ id: 1 })])],
      opts({ isCollapsed: () => true, showDraftRow: true }),
    )
    expect(rows.map((r) => r.key)).toEqual(['g:a'])
  })
})

describe('rollUpRange', () => {
  it('lấy ngày SỚM nhất và hạn MUỘN nhất trong nhóm', () => {
    expect(
      rollUpRange([
        task({ id: 1, start_date: '2026-09-05', due_date: '2026-09-09' }),
        task({ id: 2, start_date: '2026-09-01', due_date: '2026-09-03' }),
        task({ id: 3, start_date: '2026-09-20', due_date: '2026-09-30' }),
      ]),
    ).toEqual({ start: '2026-09-01', due: '2026-09-30' })
  })

  it('việc chưa có ngày KHÔNG kéo dài quãng của nhóm', () => {
    expect(
      rollUpRange([task({ id: 1, due_date: '2026-09-09' }), task({ id: 2 })]),
    ).toEqual({ start: '2026-09-09', due: '2026-09-09' })
  })

  it('cả nhóm chưa việc nào có ngày thì KHÔNG vẽ thanh nhóm', () => {
    expect(rollUpRange([task({ id: 1 }), task({ id: 2 })])).toBeNull()
    expect(rollUpRange([])).toBeNull()
  })

  it('dữ liệu nhập NGƯỢC (bắt đầu sau hạn) vẫn ra quãng dương', () => {
    expect(
      rollUpRange([task({ id: 1, start_date: '2026-09-20', due_date: '2026-09-01' })]),
    ).toEqual({ start: '2026-09-01', due: '2026-09-20' })
  })
})

describe('indexTaskRows', () => {
  it('chỉ đánh số dòng VIỆC, dòng nhóm cũng chiếm một nấc', () => {
    const rows = buildGanttRows(
      [group('a', [task({ id: 7 }), task({ id: 8 })]), group('b', [task({ id: 9 })])],
      opts(),
    )
    expect(indexTaskRows(rows)).toEqual(
      new Map([
        [7, 1],
        [8, 2],
        [9, 4],
      ]),
    )
  })
})
