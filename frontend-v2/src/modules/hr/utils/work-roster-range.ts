import { addDays, startOfMonth, startOfWeek, toISODate } from './calendar-grid'

/**
 * Khoảng ngày của màn «Xem lịch». Chỉ hai chế độ: TUẦN (mặc định) và THÁNG.
 *
 * ⚠️ Tháng hỏi đúng từ mùng 1 tới ngày cuối tháng (28–31 ngày), KHÔNG hỏi cả lưới
 * 42 ô như Lịch nghỉ: ở đây mỗi ngày là một CỘT, không có ô rìa của tháng khác,
 * và backend chặn quá 42 ngày.
 */
export type WorkRosterMode = 'week' | 'month'

export const WORK_ROSTER_MODES: readonly WorkRosterMode[] = ['week', 'month']

/** Giá trị lạ trên URL (`?mode=day`, `?mode=`) rơi về TUẦN thay vì vẽ lưới hỏng. */
export function parseRosterMode(value: string | null | undefined): WorkRosterMode {
  return value === 'month' ? 'month' : 'week'
}

/**
 * `YYYY-MM-DD` → `Date` giờ ĐỊA PHƯƠNG, hoặc `null` khi chuỗi hỏng / ngày không có
 * thật (`2026-02-31`) / năm ngoài 2000..2100 (khớp giới hạn backend).
 * Không dùng `new Date('2026-09-01')`: dạng chuỗi đó hiểu là UTC.
 */
export function parseISODate(iso: string): Date | null {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso)
  if (!match) return null
  const [y, m, d] = [Number(match[1]), Number(match[2]), Number(match[3])]
  if (y < 2000 || y > 2100) return null
  const date = new Date(y, m - 1, d)
  //  Ngày tràn (31/02 → 03/03) làm `toISODate` không còn trả lại đúng chuỗi.
  return toISODate(date) === iso ? date : null
}

export function rosterRange(anchor: Date, mode: WorkRosterMode): { from: string; to: string } {
  if (mode === 'week') {
    const start = startOfWeek(anchor)
    return { from: toISODate(start), to: toISODate(addDays(start, 6)) }
  }
  const first = startOfMonth(anchor)
  //  Ngày 0 của tháng sau = ngày cuối của tháng này.
  const last = new Date(first.getFullYear(), first.getMonth() + 1, 0)
  return { from: toISODate(first), to: toISODate(last) }
}

/**
 * Ngày «hôm nay» theo giờ Việt Nam (`YYYY-MM-DD`), không theo múi giờ máy người xem:
 * máy đặt giờ UTC lúc 00:30 sáng VN vẫn còn «hôm qua» nếu dùng `new Date()` trần.
 * `en-CA` là locale cho ra đúng dạng ISO — dựng chuỗi tay từ `formatToParts` dài hơn mà không hơn gì.
 */
export function todayInVietnamISO(now: Date = new Date()): string {
  return now.toLocaleDateString('en-CA', { timeZone: 'Asia/Ho_Chi_Minh' })
}
