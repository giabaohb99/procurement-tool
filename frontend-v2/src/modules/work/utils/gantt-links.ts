import type { WorkTask, WorkTaskLink } from '../types/work'
import { WORK_LINK_TYPE } from '../types/work'
import { MILESTONE_SIZE, ROW_HEIGHT } from './gantt-layout'
import { barGeometry, isMilestone, milestoneCenter, type GanttTimeline } from './gantt-scale'

/**
 * Hình học của MŨI TÊN PHỤ THUỘC trên Gantt (B-15) — toàn hàm thuần, có test.
 *
 * Tách hẳn khỏi component vì đây là phần dễ sai mà mắt khó bắt: một mũi tên đi
 * lệch vẫn là một mũi tên trông "có vẻ đúng", chỉ khi đối chiếu xem nó nối hai
 * việc NÀO mới lòi ra. Test giữ đúng bốn kiểu FS/SS/FF/SF nối đúng hai mép.
 *
 * Hệ tọa độ: `x` tính từ mép trái dải thời gian, `y` tính từ đỉnh vùng các hàng
 * (không tính hai hàng tiêu đề) — cùng hệ với các thanh, nên lớp SVG chỉ việc
 * nằm chồng đúng lên vùng đó.
 */

/** Đoạn cụt ra/vào mép thanh trước khi mũi tên bẻ góc (px). */
const STUB = 12

/** Đầu thanh mà một mũi tên rời đi / bay tới. */
export type LinkSide = 'start' | 'end'

/**
 * KIỂU phụ thuộc suy ra từ hai đầu người dùng chạm vào lúc kéo, đúng lối DHTMLX:
 *
 * | Rời ở | Tới ở | Kiểu |
 * | ----- | ----- | ---- |
 * | cuối  | đầu   | FS   |
 * | đầu   | đầu   | SS   |
 * | cuối  | cuối  | FF   |
 * | đầu   | cuối  | SF   |
 *
 * Để ở đây chứ không nằm trong hook kéo: đây là một BẢNG TRA thuần, mà lật nhầm
 * một ô thì người dùng kéo "xong → bắt đầu" lại ra "bắt đầu → xong" — mũi tên vẫn
 * vẽ ra, vẫn lưu được, chỉ là nói sai nghiệp vụ. Có test ghim từng ô.
 */
export function linkTypeFromSides(from: LinkSide, to: LinkSide): number {
  if (from === 'end') return to === 'start' ? WORK_LINK_TYPE.FS : WORK_LINK_TYPE.FF
  return to === 'start' ? WORK_LINK_TYPE.SS : WORK_LINK_TYPE.SF
}

/** Một đầu mũi tên. `dir` = 1: đi sang PHẢI · -1: đi sang TRÁI. */
export interface LinkAnchor {
  x: number
  y: number
  dir: 1 | -1
}

export interface LinkShape {
  /** Thuộc tính `d` của `<path>` — đường gấp khúc chỉ có đoạn ngang và dọc. */
  d: string
  /** Tam giác đầu mũi tên, dạng `points` của `<polygon>`. */
  arrow: string
  /** Điểm giữa đường — chỗ đặt nút xóa khi rê chuột vào. */
  midX: number
  midY: number
}

interface Point {
  x: number
  y: number
}

/** Tâm dọc của một hàng theo số thứ tự dòng. */
export function rowCenterY(rowIndex: number): number {
  return rowIndex * ROW_HEIGHT + ROW_HEIGHT / 2
}

/**
 * Hai mép ngang của một việc trên trục thời gian. `null` = việc chưa có ngày nên
 * không có thanh để mà nối vào.
 */
export function taskEdges(
  task: WorkTask,
  timeline: GanttTimeline,
): { left: number; right: number } | null {
  if (isMilestone(task)) {
    const center = milestoneCenter(task, timeline)
    //  Hình thoi: mép nối là hai đỉnh trái/phải của nó, không phải mép ô ngày —
    //  nối vào mép ô thì mũi tên chạm vào khoảng trống cạnh hình thoi.
    return center === null
      ? null
      : { left: center - MILESTONE_SIZE / 2, right: center + MILESTONE_SIZE / 2 }
  }
  const bar = barGeometry(task, timeline)
  return bar ? { left: bar.left, right: bar.left + bar.width } : null
}

/**
 * Hai đầu của một mũi tên, theo KIỂU phụ thuộc:
 *
 * | Kiểu | Rời việc trước ở | Vào việc sau ở |
 * | ---- | ---------------- | -------------- |
 * | FS   | mép phải (xong)  | mép trái (bắt đầu) |
 * | SS   | mép trái         | mép trái       |
 * | FF   | mép phải         | mép phải       |
 * | SF   | mép trái         | mép phải       |
 *
 * `null` khi một trong hai việc chưa có ngày — mũi tên treo lơ lửng giữa không
 * trung còn khó hiểu hơn là không vẽ gì.
 */
export function linkAnchors(
  linkType: number,
  before: { task: WorkTask; row: number },
  after: { task: WorkTask; row: number },
  timeline: GanttTimeline,
): { from: LinkAnchor; to: LinkAnchor } | null {
  const a = taskEdges(before.task, timeline)
  const b = taskEdges(after.task, timeline)
  if (!a || !b) return null

  const roiOMepPhai =
    linkType === WORK_LINK_TYPE.FS || linkType === WORK_LINK_TYPE.FF
  const vaoOMepTrai =
    linkType === WORK_LINK_TYPE.FS || linkType === WORK_LINK_TYPE.SS

  return {
    from: {
      x: roiOMepPhai ? a.right : a.left,
      y: rowCenterY(before.row),
      dir: roiOMepPhai ? 1 : -1,
    },
    to: {
      x: vaoOMepTrai ? b.left : b.right,
      y: rowCenterY(after.row),
      //  `dir` của đầu ĐẾN là chiều mũi tên BAY TỚI: vào mép trái nghĩa là nó
      //  đang bay sang phải.
      dir: vaoOMepTrai ? 1 : -1,
    },
  }
}

/**
 * Đường gấp khúc nối hai đầu — chỉ đoạn ngang và đoạn dọc, đúng lối DHTMLX.
 *
 * Hai dáng đường:
 *
 * 1. **Thuận** — hai đầu cùng chiều và việc sau nằm đủ xa về phía trước: ra khỏi
 *    mép một đoạn cụt, bẻ dọc, rồi đi thẳng vào đích. Ba đoạn, sạch nhất.
 * 2. **Vòng** — mọi trường hợp còn lại (việc sau bắt đầu TRƯỚC việc trước, hoặc
 *    hai đầu ngược chiều nhau như SS/SF). Đường luồn qua HÀNH LANG giữa hai hàng
 *    thay vì cắt ngang chính hai cái thanh nó đang nối.
 */
export function linkPath(from: LinkAnchor, to: LinkAnchor): LinkShape {
  const points = elbowPoints(from, to)
  const d = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x} ${p.y}`).join(' ')

  //  Đầu mũi tên nằm ÁP mép thanh đích, nhọn về phía nó đang bay tới.
  const tip = 7
  const arrow = [
    `${to.x},${to.y}`,
    `${to.x - to.dir * tip},${to.y - 4.5}`,
    `${to.x - to.dir * tip},${to.y + 4.5}`,
  ].join(' ')

  const mid = midOf(points)
  return { d, arrow, midX: mid.x, midY: mid.y }
}

function elbowPoints(from: LinkAnchor, to: LinkAnchor): Point[] {
  const outX = from.x + from.dir * STUB
  const inX = to.x - to.dir * STUB

  const thuan =
    from.dir === to.dir && (to.dir === 1 ? inX >= outX : inX <= outX)
  if (thuan) {
    return dedupe([
      { x: from.x, y: from.y },
      { x: outX, y: from.y },
      { x: outX, y: to.y },
      { x: to.x, y: to.y },
    ])
  }

  //  Hành lang nằm giữa hàng nguồn và hàng kế nó theo chiều đi — nửa chiều cao
  //  hàng là đúng khe trống giữa hai thanh, nên đường không đè lên thanh nào.
  const corridorY = from.y + (to.y >= from.y ? 1 : -1) * (ROW_HEIGHT / 2)
  return dedupe([
    { x: from.x, y: from.y },
    { x: outX, y: from.y },
    { x: outX, y: corridorY },
    { x: inX, y: corridorY },
    { x: inX, y: to.y },
    { x: to.x, y: to.y },
  ])
}

/** Bỏ điểm trùng nhau — đoạn dài 0 làm `<path>` mọc ra một chấm ở chỗ bẻ góc. */
function dedupe(points: Point[]): Point[] {
  return points.filter((p, i) => i === 0 || p.x !== points[i - 1].x || p.y !== points[i - 1].y)
}

/** Điểm giữa của đường gấp khúc, đo theo ĐỘ DÀI thật chứ không lấy đỉnh giữa. */
function midOf(points: Point[]): Point {
  const lengths = points.slice(1).map((p, i) =>
    Math.abs(p.x - points[i].x) + Math.abs(p.y - points[i].y),
  )
  const total = lengths.reduce((s, v) => s + v, 0)
  let walked = 0
  for (let i = 0; i < lengths.length; i += 1) {
    if (walked + lengths[i] >= total / 2) {
      const t = lengths[i] === 0 ? 0 : (total / 2 - walked) / lengths[i]
      return {
        x: points[i].x + (points[i + 1].x - points[i].x) * t,
        y: points[i].y + (points[i + 1].y - points[i].y) * t,
      }
    }
    walked += lengths[i]
  }
  return points[points.length - 1]
}

/**
 * Mũi tên nào VẼ ĐƯỢC trên biểu đồ đang hiển thị.
 *
 * Bỏ qua mũi tên có đầu không tìm thấy hàng — chuyện thường xuyên xảy ra và
 * KHÔNG phải lỗi: nhóm đang thu lại, bộ lọc đang giấu bớt việc, hoặc một đầu vừa
 * bị người khác xóa mềm (khóa ngoại chỉ bắt xóa cứng nên dòng link vẫn còn).
 */
export function visibleLinks(
  links: WorkTaskLink[],
  taskRows: Map<number, number>,
  tasks: Map<number, WorkTask>,
  timeline: GanttTimeline,
): { link: WorkTaskLink; shape: LinkShape }[] {
  const out: { link: WorkTaskLink; shape: LinkShape }[] = []
  for (const link of links) {
    const beforeRow = taskRows.get(link.predecessor_id)
    const afterRow = taskRows.get(link.successor_id)
    const before = tasks.get(link.predecessor_id)
    const after = tasks.get(link.successor_id)
    if (beforeRow === undefined || afterRow === undefined || !before || !after) continue

    const anchors = linkAnchors(
      link.link_type,
      { task: before, row: beforeRow },
      { task: after, row: afterRow },
      timeline,
    )
    if (anchors) out.push({ link, shape: linkPath(anchors.from, anchors.to) })
  }
  return out
}
