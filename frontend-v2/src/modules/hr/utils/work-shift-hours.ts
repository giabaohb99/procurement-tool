import type { WorkRosterCell } from '../types/work-roster'
import { WORK_DAY_KIND_CODE, type WorkScheduleDay } from '../types/work-schedule'
import type { HourRange } from '../types/work-shift'

/**
 * Hàm THUẦN về khung giờ của xếp ca theo ngày (duoc-CR-761). Khung là cặp giờ TRÒN `[đầu, cuối)`, 0 ≤ đầu < cuối ≤ 24
 * (24 = hết ngày, hiện "24:00"). Không khung nào = nghỉ cả ngày do xếp ca.
 */

export const HOURS_PER_DAY = 24
/** Trần số khung một ngày — khớp `MAX_SEGMENTS` của `shift_rules.py`. */
export const MAX_SEGMENTS_PER_DAY = 12

/** 8 → "08:00"; 24 → "24:00". Giờ luôn đủ HH:MM (đại ca chốt 05/10/2026), luôn 24 giờ. */
export function formatHourLabel(hour: number): string {
  return `${String(hour).padStart(2, '0')}:00`
}

/** `[8, 10]` → "08:00–10:00". */
export function formatHourRange(range: HourRange): string {
  return `${formatHourLabel(range[0])}–${formatHourLabel(range[1])}`
}

/** Nhiều khung nối bằng " · " — cùng cách hiện trên ô lưới. */
export function formatHourRanges(ranges: readonly HourRange[]): string {
  return ranges.map(formatHourRange).join(' · ')
}

/** Khung hợp lệ: số nguyên, trong 0–24, đầu < cuối. */
export function isValidRange(range: readonly number[]): boolean {
  const [start, end] = range
  return Number.isInteger(start) && Number.isInteger(end) && start >= 0 && end <= HOURS_PER_DAY && start < end
}

/** Sắp theo giờ đầu và GỘP khung chồng / chạm nhau; bỏ khung hỏng. Trả mảng mới. */
export function mergeRanges(ranges: readonly (readonly number[])[] | null | undefined): [number, number][] {
  const sorted = (ranges ?? [])
    .filter(isValidRange)
    .map(([a, b]) => [a, b] as [number, number])
    .sort((x, y) => x[0] - y[0] || x[1] - y[1])
  const out: [number, number][] = []
  for (const [start, end] of sorted) {
    const last = out[out.length - 1]
    if (last && start <= last[1]) last[1] = Math.max(last[1], end)
    else out.push([start, end])
  }
  return out
}

/**
 * Bỏ khung hỏng rồi SẮP theo giờ đầu — KHÔNG gộp: khung 08–10 và 10–12 backend trả về là hai khung người xếp cố ý tách
 * (hai việc khác nhau), mở hộp ra vẫn phải là hai dòng.
 */
export function sortRanges(ranges: readonly (readonly number[])[] | null | undefined): [number, number][] {
  return (ranges ?? [])
    .filter(isValidRange)
    .map(([a, b]) => [a, b] as [number, number])
    .sort((x, y) => x[0] - y[0] || x[1] - y[1])
}

/** "HH:MM" → số phút từ 00:00; hỏng → null. "24:00" hợp lệ (= 1440). */
function minutesOf(time: string | null | undefined): number | null {
  const match = /^(\d{1,2}):(\d{2})/.exec(time ?? '')
  if (!match) return null
  const minutes = Number(match[1]) * 60 + Number(match[2])
  return minutes >= 0 && minutes <= 24 * 60 ? minutes : null
}

const floorHour = (minutes: number) => Math.floor(minutes / 60)
const ceilHour = (minutes: number) => Math.ceil(minutes / 60)

export interface TemplateRanges {
  ranges: [number, number][]
  /** Mẫu có giờ lẻ (08:30, 17:30, trưa 12:30) nên đã làm tròn — hộp xếp ca nhắc người dùng. */
  rounded: boolean
}

/**
 * Ngày theo MẪU TUẦN → khung giờ tròn, tách quanh giờ nghỉ trưa: 08:00–17:00 trưa 12–13 → 08–12 + 13–17.
 * Giờ lẻ: đầu / cuối NGÀY làm tròn RA NGOÀI (không cắt giờ làm — 17:30 thành 18:00), mép giờ nghỉ trưa làm tròn VÀO
 * TRONG (giữ nguyên khoảng nghỉ — trưa 12:30–13:30 thành 12–14, ra 08–12 + 14–18). Báo `rounded` để hộp nhắc người
 * dùng. Ngày nghỉ / giờ hỏng → không khung.
 */
export function templateDayToRanges(
  day: Pick<WorkScheduleDay, 'day_kind' | 'start_time' | 'end_time' | 'lunch_start' | 'lunch_end'> | null | undefined,
): TemplateRanges {
  if (!day || day.day_kind === WORK_DAY_KIND_CODE.OFF) return { ranges: [], rounded: false }
  const start = minutesOf(day.start_time)
  const end = minutesOf(day.end_time)
  if (start === null || end === null || start >= end) return { ranges: [], rounded: false }
  const lunchStart = minutesOf(day.lunch_start)
  const lunchEnd = minutesOf(day.lunch_end)
  const hasLunch = lunchStart !== null && lunchEnd !== null && start < lunchStart && lunchStart < lunchEnd && lunchEnd < end
  const edges = hasLunch ? [start, lunchStart, lunchEnd, end] : [start, end]
  const rounded = edges.some((m) => m % 60 !== 0)
  const ranges: [number, number][] = hasLunch
    ? [
        [floorHour(start), floorHour(lunchStart)],
        [ceilHour(lunchEnd), ceilHour(end)],
      ]
    : [[floorHour(start), ceilHour(end)]]
  //  Ca sáng / chiều quá ngắn có thể co về rỗng sau khi làm tròn vào trong → bỏ khung rỗng.
  return { ranges: ranges.filter(([a, b]) => a < b), rounded }
}

/** Mẫu nhanh "Hành chính 08–17": 08:00–12:00 + 13:00–17:00. */
export const OFFICE_HOURS_PRESET: readonly [number, number][] = [
  [8, 12],
  [13, 17],
]

/**
 * Khung để MỞ hộp xếp ca cho một ô lưới:
 * 1. ô đã có ca riêng → đúng các khung đó, KHÔNG gộp khung liền nhau (nghỉ do xếp ca = không khung);
 * 2. có mẫu tuần ngày đó (đã nạp `/tools/effective`) → giờ của mẫu, tách quanh nghỉ trưa;
 * 3. chưa có / không đọc được mẫu → KHÔNG khung. Không tự đoán từ giờ vào–ra của ô lưới (thiếu giờ nghỉ trưa → điền
 *    sai 08–17 liền mạch rồi người dùng bấm Lưu mà không để ý); hộp tự hiện khung chờ / câu báo.
 */
export function initialRangesForCell(
  cell: Pick<WorkRosterCell, 'is_shift' | 'shift'> | undefined,
  templateDay: Parameters<typeof templateDayToRanges>[0],
): TemplateRanges {
  if (cell?.is_shift && cell.shift) return { ranges: sortRanges(cell.shift.ranges), rounded: false }
  if (templateDay) return templateDayToRanges(templateDay)
  return { ranges: [], rounded: false }
}
