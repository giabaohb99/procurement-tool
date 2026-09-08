/**
 * KÉO THẢ trên lưới lịch — phép tính thuần, không đụng React và không đụng DOM.
 *
 * Tách riêng vì đây là chỗ dễ sai nhất của cả tính năng: đổi pixel thành phút,
 * nam châm hút về mốc tròn, và giữ cho khoảng giờ không bao giờ lật ngược. Sai
 * một dấu ở đây thì người dùng kéo một cuộc họp rồi thấy nó nhảy sang hôm sau —
 * mà lỗi kiểu đó không hiện ra ở bất kỳ khẳng định nào về giao diện.
 */

import { DAY_END_HOUR, DAY_START_HOUR, GRID_MINUTES } from './room-calendar-grid'
import { toLocalInput } from './room-time'

/**
 * NAM CHÂM 15 PHÚT.
 *
 * Chuột không đủ chính xác để thả đúng 9:00 — kéo tay thật sẽ ra 8:58 hoặc
 * 9:03, và lịch họp của cả công ty đầy những con số lẻ không ai gõ ra được.
 * Chọn 15 chứ không phải 30 vì họp 45 phút là chuyện thường; chọn 15 chứ không
 * phải 5 vì 5 phút thì nam châm gần như không hút gì cả.
 */
export const SNAP_MINUTES = 15

/** Cuộc họp ngắn nhất mà kéo thả tạo ra được. Ngắn hơn nữa thì khối mất luôn chữ. */
export const MIN_DURATION_MINUTES = 15

export type DragMode = 'move' | 'resize-start' | 'resize-end'

/** Hút một số phút về bội của `SNAP_MINUTES` gần nhất. */
export function snapMinutes(minutes: number): number {
  return Math.round(minutes / SNAP_MINUTES) * SNAP_MINUTES
}

/**
 * Số phút tương ứng với quãng kéo ngang, đã hút nam châm.
 *
 * `laneWidth` là bề ngang thật của một hàng phòng (px) — trục giờ tính theo
 * phần trăm nên không có hằng số pixel nào để mượn, phải đo hàng thật.
 */
export function minutesFromDeltaX(deltaX: number, laneWidth: number): number {
  if (laneWidth <= 0) return 0
  return snapMinutes((deltaX / laneWidth) * GRID_MINUTES)
}

function shiftIso(iso: string, minutes: number): Date {
  const out = new Date(iso)
  out.setMinutes(out.getMinutes() + minutes)
  return out
}

export interface DraggedRange {
  /** Dạng `2026-09-10T09:00` — ghép tay theo giờ ĐỊA PHƯƠNG, xem `room-time.ts`. */
  start: string
  end: string
}

/**
 * Khoảng giờ mới sau khi kéo — ba kiểu kéo, một hàm.
 *
 * ⚠️ Hai mép **không được vượt qua nhau**. Kéo mép trái sang phải quá tay là
 * chuyện xảy ra trong nửa giây đầu của mọi thao tác resize; không chặn thì phiếu
 * gửi lên với `end <= start` và người dùng nhận một câu lỗi đỏ cho một thao tác
 * mà họ còn chưa thả chuột.
 */
export function draggedRange(
  startAt: string,
  endAt: string,
  mode: DragMode,
  deltaMinutes: number,
): DraggedRange {
  if (mode === 'move') {
    return {
      start: toLocalInput(shiftIso(startAt, deltaMinutes)),
      end: toLocalInput(shiftIso(endAt, deltaMinutes)),
    }
  }

  const start = new Date(startAt)
  const end = new Date(endAt)
  const spanMinutes = (end.getTime() - start.getTime()) / 60000

  if (mode === 'resize-start') {
    //  Mép trái không được đẩy quá sát mép phải.
    const capped = Math.min(deltaMinutes, spanMinutes - MIN_DURATION_MINUTES)
    return { start: toLocalInput(shiftIso(startAt, capped)), end: toLocalInput(end) }
  }

  const capped = Math.max(deltaMinutes, MIN_DURATION_MINUTES - spanMinutes)
  return { start: toLocalInput(start), end: toLocalInput(shiftIso(endAt, capped)) }
}

/**
 * Giữ khoảng giờ nằm trong khung lưới (7:00–20:00).
 *
 * Lưới chỉ vẽ được chừng đó; thả một cuộc họp ra ngoài là nó biến mất khỏi màn
 * ngay sau khi lưu, và người dùng tưởng mình vừa xóa mất phiếu.
 */
export function isInsideGrid(range: DraggedRange): boolean {
  const start = new Date(range.start)
  const end = new Date(range.end)
  //  Vắt sang ngày khác thì chặn luôn, không xét giờ: lưới vẽ MỘT ngày.
  if (start.toDateString() !== end.toDateString()) return false
  const startHour = start.getHours() + start.getMinutes() / 60
  const endHour = end.getHours() + end.getMinutes() / 60
  return startHour >= DAY_START_HOUR && endHour <= DAY_END_HOUR
}

/**
 * KẸP khoảng giờ vào trong khung lưới. `null` khi không cách nào nhét vừa.
 *
 * ⚠️ Kẹp chứ không CHẶN. Kéo quá mép là chuyện xảy ra ở mọi thao tác kéo —
 * người ta đẩy chuột tới rồi mới lùi lại. Chặn thì khối đứng im giữa chừng và
 * trông như hỏng; kẹp thì nó dừng ở mép, đúng cảm giác đụng tường.
 *
 * `null` chỉ xảy ra với cuộc họp dài hơn cả khung lưới (13 tiếng) — thứ mà kéo
 * thả không tạo ra được, nhưng dữ liệu cũ thì có. Gọi bên ngoài giữ nguyên
 * khoảng cũ khi gặp `null`.
 */
export function clampToGrid(
  range: DraggedRange,
  mode: DragMode,
  day: Date,
): DraggedRange | null {
  const start = new Date(range.start)
  const end = new Date(range.end)
  const spanMinutes = (end.getTime() - start.getTime()) / 60000

  //  ⚠️ Hai mốc dựng từ NGÀY ĐANG XEM, không phải từ ngày của kết quả kéo.
  //
  //  Lấy theo kết quả thì cái kẹp tự trôi theo: hất chuột 5.000px là +4.193
  //  phút ≈ 3 ngày, khối rơi vào 07:23 ngày 08/09 — vẫn nằm gọn trong 7:00–20:00
  //  *của ngày đó* nên kẹp thấy hợp lệ và cho qua. Phiếu lưu sang ngày khác rồi
  //  biến khỏi lưới, người dùng tưởng vừa xóa mất nó. Đo được 04/09/2026.
  const gridStart = new Date(day)
  gridStart.setHours(DAY_START_HOUR, 0, 0, 0)
  const gridEnd = new Date(day)
  gridEnd.setHours(DAY_END_HOUR, 0, 0, 0)

  if (mode === 'move') {
    if (spanMinutes > GRID_MINUTES) return null
    //  Dời CẢ khối thì giữ nguyên độ dài — đẩy vào trong, không cắt ngắn.
    let shifted = start.getTime()
    shifted = Math.max(shifted, gridStart.getTime())
    shifted = Math.min(shifted, gridEnd.getTime() - spanMinutes * 60000)
    const newStart = new Date(shifted)
    const newEnd = new Date(shifted + spanMinutes * 60000)
    return { start: toLocalInput(newStart), end: toLocalInput(newEnd) }
  }

  if (mode === 'resize-start') {
    const capped = new Date(Math.max(start.getTime(), gridStart.getTime()))
    if (end.getTime() - capped.getTime() < MIN_DURATION_MINUTES * 60000) return null
    return { start: toLocalInput(capped), end: toLocalInput(end) }
  }

  const capped = new Date(Math.min(end.getTime(), gridEnd.getTime()))
  if (capped.getTime() - start.getTime() < MIN_DURATION_MINUTES * 60000) return null
  return { start: toLocalInput(start), end: toLocalInput(capped) }
}

/** Chỉ số hàng phòng sau khi kéo dọc, đã kẹp vào hai đầu danh sách. */
export function clampRoomIndex(index: number, count: number): number {
  if (count <= 0) return 0
  return Math.min(Math.max(index, 0), count - 1)
}

/** Kéo chưa quá ngưỡng này thì tính là một cú BẤM, không phải kéo. */
export const CLICK_SLOP_PX = 4

/** Người dùng có thực sự kéo không, hay chỉ rung tay lúc bấm? */
export function isRealDrag(deltaX: number, deltaY: number): boolean {
  return Math.abs(deltaX) > CLICK_SLOP_PX || Math.abs(deltaY) > CLICK_SLOP_PX
}
