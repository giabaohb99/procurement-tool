/**
 * Giờ giấc của phiếu đặt phòng — hàm thuần, không đụng React.
 *
 * ⚠️ **Không dùng `toISOString()`.** Máy chạy ở UTC+7 nên nó trừ đi 7 giờ: chọn
 * 9:00 sáng gửi lên thành 2:00 sáng, và cuộc họp đầu giờ nhảy sang hôm trước.
 * Mọi chỗ dựng chuỗi ISO ở đây đều ghép tay theo GIỜ ĐỊA PHƯƠNG — cùng bài học
 * với `calendar-grid.toISODate`.
 */

function pad(value: number): string {
  return String(value).padStart(2, '0')
}

/** `2026-09-10T09:00` — dạng mà `<input type="datetime-local">` đọc và ghi. */
export function toLocalInput(date: Date): string {
  return (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}` +
    `T${pad(date.getHours())}:${pad(date.getMinutes())}`
  )
}

/** Chuỗi ISO gửi lên API, giữ nguyên giờ địa phương (`2026-09-10T09:00:00`). */
export function toApiTime(value: string): string {
  if (!value) return ''
  return value.length === 16 ? `${value}:00` : value
}

/** Chuỗi từ API → giá trị cho ô `datetime-local`. */
export function fromApiTime(value: string | null | undefined): string {
  return (value || '').slice(0, 16)
}

/** `09:00 – 10:30` — hai đầu giờ của một cuộc họp trong cùng ngày. */
export function formatTimeRange(startAt: string, endAt: string): string {
  const start = new Date(startAt)
  const end = new Date(endAt)
  const hhmm = (d: Date) => `${pad(d.getHours())}:${pad(d.getMinutes())}`
  //  Vắt sang ngày khác thì phải nói ra NGÀY, không thì "23:00 – 01:00" đọc như
  //  một cuộc họp đi ngược thời gian.
  if (start.toDateString() !== end.toDateString()) {
    return `${hhmm(start)} ${pad(start.getDate())}/${pad(start.getMonth() + 1)} – ` +
      `${hhmm(end)} ${pad(end.getDate())}/${pad(end.getMonth() + 1)}`
  }
  return `${hhmm(start)} – ${hhmm(end)}`
}

/** Số phút của một cuộc họp — dùng để tính chiều cao khối trên lịch. */
export function minutesBetween(startAt: string, endAt: string): number {
  return Math.max(0, (new Date(endAt).getTime() - new Date(startAt).getTime()) / 60000)
}

/**
 * Khoảng mặc định khi mở form: **giờ tròn kế tiếp, dài một tiếng**.
 *
 * Không lấy đúng "bây giờ": không ai đặt phòng cho 14:37, và để người dùng phải
 * sửa hai ô ngay khi mở form là bắt họ làm việc của máy.
 */
export function defaultSlot(now: Date): { start: string; end: string } {
  const start = new Date(now)
  start.setMinutes(0, 0, 0)
  start.setHours(start.getHours() + 1)
  const end = new Date(start)
  end.setHours(end.getHours() + 1)
  return { start: toLocalInput(start), end: toLocalInput(end) }
}
