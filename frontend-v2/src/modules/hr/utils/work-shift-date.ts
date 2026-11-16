import { formatVnDate } from './work-shift-errors'

/** Tên thứ đầy đủ, bắt đầu từ Thứ Hai (0) — lịch Việt Nam không mở đầu bằng Chủ nhật. */
export const WEEKDAY_FULL_LABELS = ['Thứ Hai', 'Thứ Ba', 'Thứ Tư', 'Thứ Năm', 'Thứ Sáu', 'Thứ Bảy', 'Chủ nhật'] as const

/** `YYYY-MM-DD` → 0 = Thứ Hai … 6 = Chủ nhật, theo lịch (không qua UTC nên không lệch ngày). Chuỗi hỏng → -1. */
export function weekdayOf(iso: string): number {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso)
  if (!match) return -1
  const day = new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3])).getDay()
  return (day + 6) % 7
}

/** "2026-11-19" → "Thứ Năm, 19/11/2026" — dòng phụ ở đầu hộp xếp ca. Chuỗi hỏng giữ nguyên. */
export function formatShiftDayLabel(iso: string): string {
  const weekday = WEEKDAY_FULL_LABELS[weekdayOf(iso)]
  return weekday ? `${weekday}, ${formatVnDate(iso)}` : iso
}
