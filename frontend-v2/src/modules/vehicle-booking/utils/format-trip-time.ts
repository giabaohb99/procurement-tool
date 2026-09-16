import { formatDate, formatTime } from '@/shared/utils/format-date'

/**
 * Khoảng thời gian một chuyến xe, gọn thành MỘT dòng đọc được.
 *
 * Backend trả `start_time` / `end_time` là chuỗi ISO tới phút
 * (`2026-09-21T10:00`). Bày thẳng chuỗi đó ra thẻ thì người dùng đọc phải hai
 * lần mới thấy chữ `T` là dấu ngăn ngày với giờ, và ngày bị lặp lại hai lần
 * trong khi gần như mọi chuyến đều đi về trong ngày.
 *
 * Bốn dạng:
 * - `Hôm nay · 10:00 – 15:00`      (đi về trong ngày, ngày là hôm nay/ngày mai)
 * - `21/09/2026 · 10:00 – 15:00`   (đi về trong ngày)
 * - `21/09/2026 10:00 → 23/09/2026 17:30` (qua ngày khác — phải ghi đủ hai mốc)
 * - `21/09/2026 · 10:00`           (chưa có giờ về)
 *
 * `now` nhận từ ngoài để bài kiểm không phụ thuộc "hôm nay" — mà "hôm nay" lại
 * chính là nhánh dễ sai nhất.
 */
export function formatTripTime(
  start: string | null | undefined,
  end: string | null | undefined,
  now: Date = new Date(),
): string {
  const from = toDate(start)
  if (!from) return '—'

  const to = toDate(end)
  const dayText = dayLabel(from, now)

  if (!to) return `${dayText} · ${formatTime(from)}`
  //  Cùng NGÀY thì chỉ ghi ngày một lần rồi hai mốc giờ. So bằng chuỗi `yyyy-mm-dd`
  //  của giờ ĐỊA PHƯƠNG, không so mốc UTC: 23:30 và 00:30 cùng đêm ở giờ Việt Nam
  //  rơi vào hai ngày UTC khác nhau.
  if (ymd(from) === ymd(to)) return `${dayText} · ${formatTime(from)} – ${formatTime(to)}`

  return `${formatDate(from)} ${formatTime(from)} → ${formatDate(to)} ${formatTime(to)}`
}

/** `Hôm nay` · `Ngày mai` · `Hôm qua`, còn lại là `dd/mm/yyyy`. */
function dayLabel(date: Date, now: Date): string {
  const offset = daysBetween(now, date)
  if (offset === 0) return 'Hôm nay'
  if (offset === 1) return 'Ngày mai'
  if (offset === -1) return 'Hôm qua'
  return formatDate(date)
}

/**
 * Số NGÀY LỊCH giữa hai mốc (b - a), không phải số khoảng-24-giờ.
 *
 * Trừ hai mốc rồi chia 86400000 là sai ở đúng chỗ cần đúng: 23:00 hôm nay và
 * 01:00 ngày mai cách nhau 2 tiếng, ra 0 ngày, nên "ngày mai" bị gọi là "hôm nay".
 */
function daysBetween(a: Date, b: Date): number {
  const dayA = new Date(a.getFullYear(), a.getMonth(), a.getDate()).getTime()
  const dayB = new Date(b.getFullYear(), b.getMonth(), b.getDate()).getTime()
  return Math.round((dayB - dayA) / 86_400_000)
}

/** `yyyy-mm-dd` theo giờ ĐỊA PHƯƠNG. */
function ymd(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

/** Chuỗi ISO → `Date`, trả `null` khi rỗng hoặc không đọc được. */
function toDate(value: string | null | undefined): Date | null {
  if (!value) return null
  const d = new Date(value)
  return Number.isNaN(d.getTime()) ? null : d
}
