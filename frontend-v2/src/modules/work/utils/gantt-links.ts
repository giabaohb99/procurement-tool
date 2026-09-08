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

/**
 * Độ vươn TỐI THIỂU của hai tay nắm cung (px).
 *
 * Hai đầu gần nhau thì `|Δx| / 2` bé tí, cung gần như một đoạn thẳng xiên cắt
 * chéo qua các hàng — đúng thứ phải tránh. Giữ sàn này để cung luôn rời mép
 * thanh theo phương NGANG rồi mới uốn.
 */
const MIN_CURVE = 40

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
  /**
   * Thuộc tính `d` của `<path>`: các đoạn NGANG và DỌC, nối nhau bằng **góc bo**
   * (`Q`) thay vì góc vuông sắc.
   */
  d: string
  /** Tam giác đầu mũi tên, dạng `points` của `<polygon>`. */
  arrow: string
  /** Điểm giữa đường — chỗ đặt nút xóa khi rê chuột vào. */
  midX: number
  midY: number
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
 * Mũi tên nào VẼ ĐƯỢC trên biểu đồ đang hiển thị.
 *
 * Bỏ qua mũi tên có đầu không tìm thấy hàng — chuyện thường xuyên xảy ra và
 * KHÔNG phải lỗi: nhóm đang thu lại, bộ lọc đang giấu bớt việc, hoặc một đầu vừa
 * bị người khác xóa mềm (khóa ngoại chỉ bắt xóa cứng nên dòng link vẫn còn).
 */
/**
 * Đường nối hai đầu — **một cung bậc ba trơn**, không có đoạn thẳng nào.
 *
 * ⚠️ Bản trước là đường gấp khúc chỉ có đoạn ngang/dọc (lối DHTMLX), sau đó bo
 * góc cho đỡ cứng. Khách vẫn bỏ 31/08/2026 và gửi ảnh Lark: *"muốn làm curved
 * như lark á"* — Lark vẽ một nét liền uốn từ mép thanh này sang mép thanh kia,
 * không hề có khúc ngang khúc dọc. Bo góc một đường gấp khúc thì vẫn là đường
 * gấp khúc, mắt vẫn đọc ra các đoạn thẳng.
 *
 * Hai tay nắm vươn theo **phương ngang** khỏi mỗi đầu (`dir` của đầu đó), nên
 * cung luôn rời mép thanh nằm ngang rồi mới uốn — đúng chỗ người ta chờ nó đi
 * ra. Độ vươn co giãn theo khoảng cách hai đầu, có SÀN `MIN_CURVE`: hai đầu gần
 * nhau thì `|Δx| / 2` bé tí, cung tụt thành một đoạn xiên cắt chéo qua các hàng.
 *
 * Việc sau nằm TRƯỚC việc trước thì không cần nhánh riêng nữa (bản gấp khúc phải
 * luồn qua một "hành lang" giữa hai hàng): hai tay nắm đẩy ngược chiều nhau tự
 * đẻ ra một cung vòng rộng, đúng dáng chữ S dài của Lark.
 */
export function linkPath(from: LinkAnchor, to: LinkAnchor): LinkShape {
  const vuon = Math.max(MIN_CURVE, Math.abs(to.x - from.x) / 2)
  const c1 = { x: from.x + from.dir * vuon, y: from.y }
  const c2 = { x: to.x - to.dir * vuon, y: to.y }
  const d =
    `M${round(from.x)} ${round(from.y)} ` +
    `C${round(c1.x)} ${round(c1.y)} ${round(c2.x)} ${round(c2.y)} ${round(to.x)} ${round(to.y)}`

  //  Đầu mũi tên nằm ÁP mép thanh đích, nhọn về phía nó đang bay tới.
  const tip = 7
  const arrow = [
    `${to.x},${to.y}`,
    `${to.x - to.dir * tip},${to.y - 4.5}`,
    `${to.x - to.dir * tip},${to.y + 4.5}`,
  ].join(' ')

  //  Điểm giữa cung tại `t = 0.5`, rút gọn từ công thức Bézier bậc ba:
  //  B(½) = (P₀ + 3P₁ + 3P₂ + P₃) / 8. Lấy trung điểm hai đầu mút thì với cung
  //  vòng ngược nó rơi hẳn ra ngoài đường, viên mã kiểu treo giữa không trung.
  return {
    d,
    arrow,
    midX: (from.x + 3 * c1.x + 3 * c2.x + to.x) / 8,
    midY: (from.y + 3 * c1.y + 3 * c2.y + to.y) / 8,
  }
}

/** Một chữ số thập phân là quá đủ cho toạ độ pixel — chuỗi `d` ngắn lại một nửa. */
function round(v: number): number {
  return Math.round(v * 10) / 10
}

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
