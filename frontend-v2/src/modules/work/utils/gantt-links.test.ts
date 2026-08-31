import { describe, expect, it } from 'vitest'

import type { WorkTask, WorkTaskLink } from '../types/work'
import { WORK_LINK_TYPE, WORK_TASK_KIND, WORK_TASK_STATUS } from '../types/work'
import { MILESTONE_SIZE, ROW_HEIGHT } from './gantt-layout'
import { linkAnchors, linkPath, rowCenterY, taskEdges, visibleLinks } from './gantt-links'
import { barGeometry, buildTimeline } from './gantt-scale'

/**
 * Mũi tên phụ thuộc (B-15). Một mũi tên nối SAI hai việc vẫn là một mũi tên
 * trông "có vẻ đúng" — mắt không bắt được, chỉ khi dò xem nó đi từ đâu tới đâu
 * mới lòi ra. Nên bốn kiểu FS/SS/FF/SF được ghim từng cái ở đây.
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

function link(patch: Partial<WorkTaskLink> = {}): WorkTaskLink {
  return {
    id: 1, list_id: 1, predecessor_id: 1, successor_id: 2,
    link_type: WORK_LINK_TYPE.FS, lag_days: 0,
    ...patch,
  }
}

const A = task({ id: 1, start_date: '2026-09-01', due_date: '2026-09-05' })
const B = task({ id: 2, start_date: '2026-09-10', due_date: '2026-09-15' })
const timeline = buildTimeline([A, B], 'day', '2026-09-01')

function edgesOf(t: WorkTask) {
  const bar = barGeometry(t, timeline)
  if (!bar) throw new Error('việc dùng trong test phải có ngày')
  return { left: bar.left, right: bar.left + bar.width }
}

describe('taskEdges', () => {
  it('việc thường lấy hai mép của thanh', () => {
    expect(taskEdges(A, timeline)).toEqual(edgesOf(A))
  })

  it('CỘT MỐC lấy hai đỉnh của hình thoi, không phải mép ô ngày', () => {
    //  Nối vào mép ô thì mũi tên chạm khoảng trống cạnh hình thoi, hở một quãng
    //  bằng nửa ô ngày.
    const moc = task({ id: 3, kind: WORK_TASK_KIND.MILESTONE, due_date: '2026-09-10' })
    const canh = taskEdges(moc, timeline)
    expect(canh).not.toBeNull()
    expect((canh as { right: number }).right - (canh as { left: number }).left).toBe(MILESTONE_SIZE)
  })

  it('việc chưa có ngày thì không có mép nào để nối', () => {
    expect(taskEdges(task({ id: 4 }), timeline)).toBeNull()
  })
})

describe('linkAnchors', () => {
  const before = { task: A, row: 0 }
  const after = { task: B, row: 1 }

  it('FS rời mép PHẢI việc trước, vào mép TRÁI việc sau', () => {
    const a = linkAnchors(WORK_LINK_TYPE.FS, before, after, timeline)
    expect(a?.from.x).toBe(edgesOf(A).right)
    expect(a?.to.x).toBe(edgesOf(B).left)
    expect(a?.from.dir).toBe(1)
    expect(a?.to.dir).toBe(1)
  })

  it('SS nối hai mép TRÁI', () => {
    const a = linkAnchors(WORK_LINK_TYPE.SS, before, after, timeline)
    expect(a?.from.x).toBe(edgesOf(A).left)
    expect(a?.to.x).toBe(edgesOf(B).left)
    expect(a?.from.dir).toBe(-1)
  })

  it('FF nối hai mép PHẢI', () => {
    const a = linkAnchors(WORK_LINK_TYPE.FF, before, after, timeline)
    expect(a?.from.x).toBe(edgesOf(A).right)
    expect(a?.to.x).toBe(edgesOf(B).right)
    expect(a?.to.dir).toBe(-1)
  })

  it('SF rời mép TRÁI, vào mép PHẢI', () => {
    const a = linkAnchors(WORK_LINK_TYPE.SF, before, after, timeline)
    expect(a?.from.x).toBe(edgesOf(A).left)
    expect(a?.to.x).toBe(edgesOf(B).right)
  })

  it('hai đầu đặt đúng TÂM hàng của mình', () => {
    const a = linkAnchors(WORK_LINK_TYPE.FS, before, { task: B, row: 4 }, timeline)
    expect(a?.from.y).toBe(ROW_HEIGHT / 2)
    expect(a?.to.y).toBe(rowCenterY(4))
  })

  it('một đầu chưa có ngày thì KHÔNG vẽ mũi tên treo lơ lửng', () => {
    const rong = { task: task({ id: 9 }), row: 2 }
    expect(linkAnchors(WORK_LINK_TYPE.FS, before, rong, timeline)).toBeNull()
    expect(linkAnchors(WORK_LINK_TYPE.FS, rong, after, timeline)).toBeNull()
  })
})

describe('linkPath', () => {
  it('đường chỉ có đoạn NGANG và đoạn DỌC — không có đoạn xiên', () => {
    const shape = linkPath({ x: 100, y: 18, dir: 1 }, { x: 300, y: 90, dir: 1 })
    const points = shape.d
      .split(/[ML]/)
      .filter(Boolean)
      .map((p) => p.trim().split(' ').map(Number))

    for (let i = 1; i < points.length; i += 1) {
      const doiX = points[i][0] !== points[i - 1][0]
      const doiY = points[i][1] !== points[i - 1][1]
      expect(doiX && doiY).toBe(false)
    }
  })

  it('việc sau nằm TRƯỚC việc trước thì đường vòng qua hành lang giữa hai hàng', () => {
    //  Không có nhánh vòng thì đường cắt thẳng qua chính hai cái thanh nó nối.
    const shape = linkPath({ x: 400, y: 18, dir: 1 }, { x: 100, y: 90, dir: 1 })
    const ys = shape.d.match(/-?\d+(\.\d+)?(?= |$)/g)?.map(Number) ?? []
    expect(ys).toContain(18 + ROW_HEIGHT / 2)
  })

  it('đầu nhọn quay đúng chiều mũi tên đang bay tới', () => {
    const phai = linkPath({ x: 10, y: 18, dir: 1 }, { x: 200, y: 90, dir: 1 })
    const trai = linkPath({ x: 200, y: 18, dir: -1 }, { x: 10, y: 90, dir: -1 })
    //  Bay sang phải: hai đỉnh đuôi nằm BÊN TRÁI mũi nhọn, và ngược lại.
    expect(phai.arrow).toContain('193,')
    expect(trai.arrow).toContain('17,')
  })

  it('điểm giữa nằm TRÊN đường, không phải giữa hai đầu mút', () => {
    const shape = linkPath({ x: 0, y: 18, dir: 1 }, { x: 200, y: 90, dir: 1 })
    expect(shape.midX).toBeGreaterThanOrEqual(0)
    expect(shape.midX).toBeLessThanOrEqual(200)
    expect(shape.midY).toBeGreaterThanOrEqual(18)
    expect(shape.midY).toBeLessThanOrEqual(90)
  })
})

describe('visibleLinks', () => {
  const tasks = new Map([
    [A.id, A],
    [B.id, B],
  ])

  it('vẽ mũi tên khi cả hai đầu đang hiện', () => {
    const rows = new Map([
      [1, 0],
      [2, 1],
    ])
    expect(visibleLinks([link()], rows, tasks, timeline)).toHaveLength(1)
  })

  it('bỏ qua mũi tên có đầu bị ẨN (nhóm đang thu, hoặc bộ lọc đang giấu việc)', () => {
    //  Không phải lỗi: nhóm thu lại là chuyện thường. Ném lỗi hay vẽ mũi tên trỏ
    //  vào hàng 0 đều tệ hơn hẳn.
    const rows = new Map([[1, 0]])
    expect(visibleLinks([link()], rows, tasks, timeline)).toHaveLength(0)
  })

  it('bỏ qua mũi tên trỏ tới việc đã bị XÓA MỀM (dòng link vẫn còn dưới CSDL)', () => {
    const rows = new Map([
      [1, 0],
      [2, 1],
    ])
    const conMotBen = new Map([[A.id, A]])
    expect(visibleLinks([link()], rows, conMotBen, timeline)).toHaveLength(0)
  })

  it('danh sách rỗng không nổ', () => {
    expect(visibleLinks([], new Map(), new Map(), timeline)).toEqual([])
  })
})
