import { describe, expect, it } from 'vitest'

import type { WorkTask, WorkTaskLink } from '../types/work'
import { WORK_LINK_TYPE, WORK_TASK_KIND, WORK_TASK_STATUS } from '../types/work'
import { MILESTONE_SIZE, ROW_HEIGHT } from './gantt-layout'
import {
  linkAnchors,
  linkPath,
  linkTypeFromSides,
  rowCenterY,
  taskEdges,
  visibleLinks,
} from './gantt-links'
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

describe('linkTypeFromSides', () => {
  //  Bảng tra thuần: lật nhầm một ô thì người dùng kéo "xong → bắt đầu" lại ra
  //  "bắt đầu → xong". Mũi tên vẫn vẽ, vẫn lưu được, chỉ là nói SAI nghiệp vụ —
  //  không có gì trên màn hình tố cáo, nên ghim từng ô.
  it.each([
    ['end', 'start', WORK_LINK_TYPE.FS],
    ['start', 'start', WORK_LINK_TYPE.SS],
    ['end', 'end', WORK_LINK_TYPE.FF],
    ['start', 'end', WORK_LINK_TYPE.SF],
  ] as const)('rời ở %s, tới ở %s thì ra kiểu %i', (from, to, expected) => {
    expect(linkTypeFromSides(from, to)).toBe(expected)
  })

  it('bốn tổ hợp cho ra bốn kiểu KHÁC nhau, không cái nào trùng', () => {
    const sides = ['start', 'end'] as const
    const all = sides.flatMap((f) => sides.map((t) => linkTypeFromSides(f, t)))
    expect(new Set(all).size).toBe(4)
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

/** Bóc `[fromX, c1X, toX, c2X]` khỏi chuỗi `d` của một cung bậc ba. */
function doc(shape: { d: string }): [number, number, number, number] {
  const m = shape.d.match(
    /^M([\d.-]+) [\d.-]+ C([\d.-]+) [\d.-]+ ([\d.-]+) [\d.-]+ ([\d.-]+) [\d.-]+$/,
  )
  if (!m) throw new Error(`Chuỗi d không phải một cung bậc ba: ${shape.d}`)
  const [fromX, c1X, c2X, toX] = m.slice(1).map(Number)
  return [fromX, c1X, toX, c2X]
}

describe('linkPath', () => {
  it('đường là MỘT cung bậc ba trơn — không còn đoạn gấp khúc nào', () => {
    //  Khách 31/08/2026 gửi ảnh Lark: *"muốn làm curved như lark á"*. Bản gấp
    //  khúc (kể cả đã bo góc) vẫn đọc ra các đoạn thẳng, nên bỏ hẳn.
    const shape = linkPath({ x: 100, y: 18, dir: 1 }, { x: 300, y: 90, dir: 1 })
    expect(shape.d).toMatch(/^M[\d.-]+ [\d.-]+ C[\d.-]+ [\d.-]+ [\d.-]+ [\d.-]+ [\d.-]+ [\d.-]+$/)
    expect(shape.d).not.toContain('L')
    expect(shape.d).not.toContain('Q')
  })

  it('tay nắm vươn NGANG theo đúng chiều của từng đầu', () => {
    //  Nhờ vậy cung rời mép thanh theo phương ngang rồi mới uốn — vươn sai chiều
    //  là cung thúc ngược vào trong chính cái thanh nó vừa rời.
    const [, c1x, , c2x] = doc(linkPath({ x: 100, y: 18, dir: 1 }, { x: 300, y: 90, dir: 1 }))
    expect(c1x).toBeGreaterThan(100)
    expect(c2x).toBeLessThan(300)

    const [, t1x, , t2x] = doc(linkPath({ x: 300, y: 18, dir: -1 }, { x: 100, y: 90, dir: -1 }))
    expect(t1x).toBeLessThan(300)
    expect(t2x).toBeGreaterThan(100)
  })

  it('hai đầu gần nhau vẫn có cung, không tụt thành đoạn xiên', () => {
    //  `|Δx| / 2` của hai đầu sát nhau là vài pixel; không có sàn `MIN_CURVE` thì
    //  cung thành một gạch chéo cắt ngang các hàng.
    const [fx, c1x] = doc(linkPath({ x: 100, y: 18, dir: 1 }, { x: 104, y: 90, dir: 1 }))
    expect(c1x - fx).toBeGreaterThanOrEqual(40)
  })

  it('việc sau nằm TRƯỚC việc trước thì cung VÒNG rộng ra, không cắt thẳng', () => {
    //  Hai tay nắm đẩy ngược chiều nhau tự đẻ ra cung vòng — bản gấp khúc phải
    //  luồn qua một "hành lang" riêng giữa hai hàng mới tránh được hai cái thanh.
    const [fx, c1x, tx, c2x] = doc(linkPath({ x: 400, y: 18, dir: 1 }, { x: 100, y: 90, dir: 1 }))
    expect(c1x).toBeGreaterThan(fx)
    expect(c2x).toBeLessThan(tx)
    //  Hai tay nắm vắt chéo qua nhau — đó chính là chỗ cung phình thành chữ S.
    expect(c2x).toBeLessThan(c1x)
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
