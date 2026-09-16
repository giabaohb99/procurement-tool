/**
 * Đọc/định dạng mốc thời gian của phiếu đặt xe.
 *
 * Backend lưu `start_time` / `end_time` là chuỗi ISO tới PHÚT (`'2026-09-10T05:00'`,
 * xem `service._now()`), không phải `Date`. Cắt chuỗi rẻ hơn và tránh hẳn chuyện
 * `new Date()` dịch múi giờ — mốc trong phiếu là giờ địa phương đã chốt.
 */

/** '2026-09-10T05:00' -> '05:00'; không có giờ -> ''. */
export function timeOf(iso: string): string {
  const i = iso.indexOf('T')
  return i >= 0 ? iso.slice(i + 1, i + 6) : ''
}

/** '2026-09-10T05:00' -> '10/09'; rỗng -> ''. */
export function dayMonthOf(iso: string): string {
  return iso ? `${iso.slice(8, 10)}/${iso.slice(5, 7)}` : ''
}

/**
 * Khoảng thời gian cho thẻ hover trên lịch. Chuyến TRONG NGÀY chỉ cần giờ
 * (`09:30 – 17:00`); chuyến SANG NGÀY phải ghi ngày ở CẢ HAI đầu
 * (`04/09 09:30 → 05/09 07:00`) — ghi ngày một đầu thì người đọc không biết giờ
 * đầu kia thuộc ngày nào.
 */
export function formatBookingRange(startIso: string, endIso: string): string {
  const startTime = timeOf(startIso)
  const endTime = timeOf(endIso)
  const startDay = dayMonthOf(startIso)
  const endDay = dayMonthOf(endIso)

  if (!startIso && !endIso) return '—'
  if (!endIso) return startTime || startDay || '—'
  if (startDay === endDay) {
    return endTime && endTime !== startTime ? `${startTime} – ${endTime}` : startTime || '—'
  }
  return `${startDay} ${startTime} → ${endDay} ${endTime}`.replace(/\s+/g, ' ').trim()
}
