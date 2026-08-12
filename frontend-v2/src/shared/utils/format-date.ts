/**
 * Ngày giờ theo chuẩn hiển thị của hệ: dd/mm/yyyy.
 * Backend trả chuỗi ISO (`2026-08-11` hoặc `2026-08-11T09:30:00`).
 */

/** `11/08/2026`. */
export function formatDate(value: string | Date | null | undefined): string {
  const date = toDate(value)
  if (!date) return ''
  return date.toLocaleDateString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

/** `11/08/2026 09:30`. */
export function formatDateTime(value: string | Date | null | undefined): string {
  const date = toDate(value)
  if (!date) return ''
  return `${formatDate(date)} ${date.toLocaleTimeString('vi-VN', {
    hour: '2-digit',
    minute: '2-digit',
  })}`
}

/** `Thứ Tư, 12.08.2026` — dạng đầy đủ dùng ở màn chọn phân hệ. */
export function formatWeekdayDate(value: string | Date | null | undefined): string {
  const date = toDate(value)
  if (!date) return ''
  const weekday = date.toLocaleDateString('vi-VN', { weekday: 'long' })
  // Viết hoa chữ đầu: vi-VN trả "thứ tư", cần "Thứ Tư" cho tiêu đề.
  const label = weekday.replace(/(^|\s)\p{Ll}/gu, (c) => c.toUpperCase())
  const [day, month, year] = [
    String(date.getDate()).padStart(2, '0'),
    String(date.getMonth() + 1).padStart(2, '0'),
    date.getFullYear(),
  ]
  return `${label}, ${day}.${month}.${year}`
}

/** `2026-08-11` — dạng dùng cho `<input type="date">` và tham số query. */
export function toDateInputValue(value: string | Date | null | undefined): string {
  const date = toDate(value)
  if (!date) return ''
  const offsetMs = date.getTimezoneOffset() * 60_000
  return new Date(date.getTime() - offsetMs).toISOString().slice(0, 10)
}

function toDate(value: string | Date | null | undefined): Date | null {
  if (!value) return null
  const date = value instanceof Date ? value : new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}
