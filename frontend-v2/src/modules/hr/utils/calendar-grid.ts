import type { Holiday } from '../types/leave'

/**
 * Dựng lưới ngày cho màn LỊCH NGHỈ — phần tính toán thuần, không dính React.
 *
 * ⚠️ **Mọi phép đổi ngày → chuỗi đều cắt tay theo giờ ĐỊA PHƯƠNG, tuyệt đối
 * không dùng `toISOString()`.** Hàm đó quy về UTC, mà Việt Nam lệch +7: ngày
 * 01/09 lúc 00:00 giờ VN thành `2026-08-31` trong chuỗi ISO, và cả cái lịch
 * lệch đi một ngày. Backend cũng so bằng chuỗi `YYYY-MM-DD` nên lệch ở đây là
 * lệch tới tận câu truy vấn.
 */

export type CalendarMode = 'day' | 'week' | 'month'

/** Nhãn cột, bắt đầu từ THỨ HAI — lịch Việt Nam không mở đầu bằng Chủ nhật. */
export const WEEKDAY_LABELS = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'] as const

/** Lưới tháng luôn 6 hàng × 7 cột. Xem `buildMonthGrid`. */
export const MONTH_GRID_WEEKS = 6

export function toISODate(d: Date): string {
  const m = `${d.getMonth() + 1}`.padStart(2, '0')
  const day = `${d.getDate()}`.padStart(2, '0')
  return `${d.getFullYear()}-${m}-${day}`
}

/** Bản sao đã đặt về 00:00 — tránh sửa nhầm đối tượng gốc của người gọi. */
function atMidnight(date: Date): Date {
  const d = new Date(date)
  d.setHours(0, 0, 0, 0)
  return d
}

export function addDays(date: Date, days: number): Date {
  const d = atMidnight(date)
  d.setDate(d.getDate() + days)
  return d
}

/**
 * Thứ Hai của tuần chứa `date`.
 *
 * `getDay()` trả 0 cho Chủ nhật nên phải nắn: `(day + 6) % 7` biến Thứ Hai
 * thành 0 và Chủ nhật thành 6.
 */
export function startOfWeek(date: Date): Date {
  const d = atMidnight(date)
  return addDays(d, -((d.getDay() + 6) % 7))
}

export function startOfMonth(date: Date): Date {
  const d = atMidnight(date)
  d.setDate(1)
  return d
}

/**
 * Dịch mốc đang xem đi `step` đơn vị của chế độ hiện tại.
 *
 * ⚠️ Chế độ THÁNG cộng tháng chứ không cộng 30 ngày, và phải chống **ngày tràn**:
 * `new Date(2026, 0, 31)` cộng một tháng theo kiểu ngây thơ ra 03/03 (vì tháng 2
 * không có ngày 31). Đặt về ngày 1 trước khi cộng thì không bao giờ tràn.
 */
export function shiftAnchor(anchor: Date, mode: CalendarMode, step: number): Date {
  if (mode === 'day') return addDays(anchor, step)
  if (mode === 'week') return addDays(anchor, step * 7)

  const d = startOfMonth(anchor)
  d.setMonth(d.getMonth() + step)
  return d
}

/**
 * Khoảng ngày cần HỎI BACKEND cho chế độ đang xem.
 *
 * ⚠️ Chế độ tháng hỏi theo **cả lưới 42 ô**, không phải theo mốc đầu/cuối tháng:
 * lưới có chừa chỗ cho mấy ngày cuối tháng trước và đầu tháng sau, và những ô đó
 * cũng phải hiện ai nghỉ. Hỏi đúng phạm vi tháng thì các ô rìa luôn trống, đọc
 * ra thành "hôm đó không ai nghỉ" — sai.
 */
export function rangeOf(anchor: Date, mode: CalendarMode): { from: string; to: string } {
  if (mode === 'day') {
    const iso = toISODate(anchor)
    return { from: iso, to: iso }
  }
  if (mode === 'week') {
    const start = startOfWeek(anchor)
    return { from: toISODate(start), to: toISODate(addDays(start, 6)) }
  }

  const grid = buildMonthGrid(anchor)
  return { from: toISODate(grid[0].date), to: toISODate(grid[grid.length - 1].date) }
}

export function buildWeekDays(anchor: Date): Date[] {
  const start = startOfWeek(anchor)
  return Array.from({ length: 7 }, (_, i) => addDays(start, i))
}

export interface MonthCell {
  date: Date
  /** `false` = ngày của tháng trước / tháng sau, chỉ để lấp đầy lưới. */
  inMonth: boolean
}

/**
 * Lưới tháng: **luôn 6 hàng × 7 cột = 42 ô**, bắt đầu từ Thứ Hai.
 *
 * ⚠️ Cố định 6 hàng chứ không cắt theo số tuần thật. Một tháng cần 4, 5 hoặc 6
 * hàng tùy nó bắt đầu vào thứ mấy (tháng 2 năm thường bắt đầu Thứ Hai chỉ cần 4);
 * để số hàng đổi theo tháng thì bấm sang tháng sau là cả lưới nhảy cao thấp, và
 * mọi thứ bên dưới giật theo. Chiều cao ô do CSS chia đều 6 hàng nên nó ổn định.
 */
export function buildMonthGrid(anchor: Date): MonthCell[] {
  const first = startOfMonth(anchor)
  const gridStart = startOfWeek(first)
  const month = first.getMonth()

  return Array.from({ length: MONTH_GRID_WEEKS * 7 }, (_, i) => {
    const date = addDays(gridStart, i)
    return { date, inMonth: date.getMonth() === month }
  })
}

/** Nhãn của khoảng đang xem — hiện giữa hai nút mũi tên. */
export function rangeLabel(anchor: Date, mode: CalendarMode): string {
  if (mode === 'day') {
    return `${WEEKDAY_LABELS[(anchor.getDay() + 6) % 7]}, ${anchor.getDate()}/${anchor.getMonth() + 1}/${anchor.getFullYear()}`
  }
  if (mode === 'week') {
    const start = startOfWeek(anchor)
    const end = addDays(start, 6)
    //  Tuần vắt qua hai tháng thì phải ghi cả hai, nếu không "1 – 7" đọc ra là
    //  một tuần trong cùng một tháng.
    const sameMonth = start.getMonth() === end.getMonth()
    const left = sameMonth
      ? `${start.getDate()}`
      : `${start.getDate()}/${start.getMonth() + 1}`
    return `${left} – ${end.getDate()}/${end.getMonth() + 1}/${end.getFullYear()}`
  }
  return `Tháng ${anchor.getMonth() + 1}/${anchor.getFullYear()}`
}

/**
 * Tên các ngày lễ rơi vào `iso`.
 *
 * ⚠️ `is_recurring` so theo **ngày/tháng, bỏ qua năm**: Tết Dương lịch và Quốc
 * khánh nhập một lần rồi lặp mãi. Tết Âm và Giỗ Tổ trôi theo lịch âm nên không
 * lặp được — mỗi năm nhập một dòng riêng, và những dòng đó so đủ cả năm.
 *
 * Trả về mảng chứ không một tên: hai pháp nhân có thể khai hai ngày lễ khác nhau
 * trùng ngày (nhà máy nghỉ bù khác văn phòng), và giấu bớt một cái đi thì lịch
 * nói sai với một nửa công ty.
 */
export function holidayNamesOn(holidays: Holiday[], iso: string): string[] {
  const [, month, day] = iso.split('-')
  const names: string[] = []

  for (const h of holidays) {
    if (!h.is_active) continue
    const [hYear, hMonth, hDay] = h.date.split('-')
    const hit = h.is_recurring
      ? hMonth === month && hDay === day
      : `${hYear}-${hMonth}-${hDay}` === iso
    if (hit && !names.includes(h.name)) names.push(h.name)
  }
  return names
}

/**
 * `true` khi ngày đó KHÔNG tính vào phép — với DEGO Holding là **chỉ Chủ nhật**.
 *
 * ⚠️ Công ty **làm cả ngày thứ Bảy** (chốt 04/09/2026), nên T7 tô như ngày làm
 * việc bình thường. Luật này phải khớp `WEEKEND_DAYS` ở
 * `backend/app/modules/leave/workday_service.py`: lịch tô T7 màu nghỉ trong khi
 * backend vẫn trừ phép ngày đó thì người xem đọc màu rồi tin nhầm, và chỉ phát
 * hiện khi quỹ phép hụt mất mấy ngày.
 *
 * `getDay()` của JS trả **0 cho Chủ nhật** (khác `weekday()` của Python trả 6) —
 * đừng chép thẳng con số từ backend sang.
 */
export function isWeekend(date: Date): boolean {
  return date.getDay() === 0
}
