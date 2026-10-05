import { WORK_DAY_KIND_CODE, type WorkScheduleDay } from '../types/work-schedule'

/** Nhãn thứ, chỉ số = `weekday` backend (0 = Thứ Hai). */
export const WEEKDAY_LABELS = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'] as const

export const STANDARD_LUNCH = { start: '12:00', end: '13:00' } as const

const DEFAULT_START = '08:00'
const DEFAULT_END = '17:00'
const DEFAULT_LUNCH_START = STANDARD_LUNCH.start
const DEFAULT_LUNCH_END = STANDARD_LUNCH.end
const MORNING_END = '12:00'
const AFTERNOON_START = '13:00'

/**
 * Giờ từ backend (`"08:00:00"`) hoặc người nhập (`"8:00"`) -> `"HH:MM"` cho
 * `<input type="time">`. Không đọc ra giờ thì trả `''` (ô trống), không ném lỗi.
 */
export function toTimeInput(value: unknown): string {
  if (typeof value !== 'string') return ''
  const match = /^(\d{1,2}):(\d{2})(?::\d{2})?$/.exec(value.trim())
  if (!match) return ''
  const hour = Number(match[1])
  const minute = Number(match[2])
  if (hour > 23 || minute > 59) return ''
  return `${String(hour).padStart(2, '0')}:${match[2]}`
}

/** Ô giờ trống -> `null` để gửi backend (OFF / buổi không có giờ trưa). */
function toTimeOrNull(value: unknown): string | null {
  return toTimeInput(value) || null
}

function emptyDay(weekday: number, dayKind: number): WorkScheduleDay {
  return {
    weekday,
    day_kind: dayKind,
    start_time: null,
    end_time: null,
    lunch_start: null,
    lunch_end: null,
  }
}

/** Mẫu mới: T2–T7 cả ngày 08:00–17:00 nghỉ trưa 12:00–13:00, CN nghỉ — khớp mặc định hệ thống. */
export function buildDefaultWeek(): WorkScheduleDay[] {
  return WEEKDAY_LABELS.map((_, weekday) =>
    weekday === 6
      ? emptyDay(weekday, WORK_DAY_KIND_CODE.OFF)
      : {
          weekday,
          day_kind: WORK_DAY_KIND_CODE.FULL,
          start_time: DEFAULT_START,
          end_time: DEFAULT_END,
          lunch_start: DEFAULT_LUNCH_START,
          lunch_end: DEFAULT_LUNCH_END,
        },
  )
}

/** Các thứ (0..6) THỰC SỰ có mặt trong mảng — để phân biệt «backend không trả thứ đó» với «thứ đó nghỉ». */
export function presentWeekdays(days: unknown): Set<number> {
  const present = new Set<number>()
  if (!Array.isArray(days)) return present
  for (const raw of days as Partial<WorkScheduleDay>[]) {
    const weekday = Number(raw?.weekday)
    if (Number.isInteger(weekday) && weekday >= 0 && weekday <= 6) present.add(weekday)
  }
  return present
}

/**
 * Đủ 7 hàng theo thứ tự T2..CN từ mảng bất kỳ: thiếu thứ nào thì hàng đó là
 * «Nghỉ», thứ lạ (ngoài 0..6) bị bỏ, trùng thì dòng sau thắng. Giờ được chuẩn
 * hóa về "HH:MM". Backend lỗi dữ liệu cũng không làm bảng nổ.
 */
export function fillWeek(days: unknown): WorkScheduleDay[] {
  const byWeekday = new Map<number, WorkScheduleDay>()
  if (Array.isArray(days)) {
    for (const raw of days as Partial<WorkScheduleDay>[]) {
      const weekday = Number(raw?.weekday)
      if (!Number.isInteger(weekday) || weekday < 0 || weekday > 6) continue
      byWeekday.set(weekday, {
        weekday,
        day_kind: Number(raw.day_kind) || WORK_DAY_KIND_CODE.OFF,
        start_time: toTimeOrNull(raw.start_time),
        end_time: toTimeOrNull(raw.end_time),
        lunch_start: toTimeOrNull(raw.lunch_start),
        lunch_end: toTimeOrNull(raw.lunch_end),
      })
    }
  }
  return WEEKDAY_LABELS.map(
    (_, weekday) => byWeekday.get(weekday) ?? emptyDay(weekday, WORK_DAY_KIND_CODE.OFF),
  )
}

/**
 * Đổi loại ngày của MỘT hàng. Loại ngày THỰC SỰ đổi thì đặt lại giờ chuẩn của loại
 * mới, KHÔNG giữ giờ cũ: Cả ngày 08–17 đổi sang Buổi sáng mà giữ nguyên thì thành
 * «sáng 08–17» — nghỉ phép theo giờ ở backend tính sai im lặng. Cùng loại (chọn lại
 * đúng mục đang chọn) thì giữ giờ người dùng đã sửa.
 *
 *  - Cả ngày:   08:00–17:00, nghỉ trưa 12:00–13:00
 *  - Buổi sáng: 08:00–12:00, không nghỉ trưa
 *  - Buổi chiều: 13:00–17:00, không nghỉ trưa
 *  - Nghỉ:      cả bốn ô giờ null
 */
export function normalizeDayOnKindChange(day: WorkScheduleDay, dayKind: number): WorkScheduleDay {
  if (day.day_kind === dayKind) return { ...day }
  switch (dayKind) {
    case WORK_DAY_KIND_CODE.FULL:
      return {
        weekday: day.weekday,
        day_kind: dayKind,
        start_time: DEFAULT_START,
        end_time: DEFAULT_END,
        lunch_start: DEFAULT_LUNCH_START,
        lunch_end: DEFAULT_LUNCH_END,
      }
    case WORK_DAY_KIND_CODE.MORNING:
      return { ...emptyDay(day.weekday, dayKind), start_time: DEFAULT_START, end_time: MORNING_END }
    case WORK_DAY_KIND_CODE.AFTERNOON:
      return { ...emptyDay(day.weekday, dayKind), start_time: AFTERNOON_START, end_time: DEFAULT_END }
    default:
      return emptyDay(day.weekday, dayKind)
  }
}

/** Công của một ngày: cả ngày 1, nửa ngày 0,5, nghỉ 0 (khớp `day_capacity` backend). */
export function dayCredit(dayKind: number): number {
  if (dayKind === WORK_DAY_KIND_CODE.FULL) return 1
  if (dayKind === WORK_DAY_KIND_CODE.MORNING || dayKind === WORK_DAY_KIND_CODE.AFTERNOON) return 0.5
  return 0
}

/** Tổng ngày công một tuần. Mảng rỗng / thiếu thứ -> tính phần có mặt. */
export function sumWeeklyWorkdays(days: unknown): number {
  return fillWeek(days).reduce((total, day) => total + dayCredit(day.day_kind), 0)
}

/** 5.5 -> "5,5" (kiểu Việt, không phụ thuộc ICU của môi trường chạy). */
export function formatWorkdays(value: number): string {
  return String(value).replace('.', ',')
}

/** Mẫu điền nhanh cả tuần ở đầu bảng 7 ngày. */
export const WEEK_PRESETS = [
  { key: 'office', label: 'T2–T6 hành chính' },
  { key: 'sixDays', label: 'T2–T7' },
  { key: 'saturdayMorning', label: 'T7 nửa buổi sáng' },
] as const

export type WeekPresetKey = (typeof WEEK_PRESETS)[number]['key']

/** Ngày `kind` với giờ chuẩn của loại đó (dùng lại `normalizeDayOnKindChange` để không lệch giờ chuẩn). */
function standardDay(weekday: number, kind: number): WorkScheduleDay {
  return normalizeDayOnKindChange(emptyDay(weekday, WORK_DAY_KIND_CODE.OFF), kind)
}

/**
 * Điền nhanh cả tuần:
 *  - office: T2–T6 cả ngày giờ chuẩn, T7 + CN nghỉ
 *  - sixDays: T2–T7 cả ngày giờ chuẩn, CN nghỉ
 *  - saturdayMorning: CHỈ đổi T7 thành buổi sáng, các thứ khác giữ nguyên
 */
export function applyWeekPreset(week: WorkScheduleDay[], preset: WeekPresetKey): WorkScheduleDay[] {
  const filled = fillWeek(week)
  switch (preset) {
    case 'office':
      return filled.map((_, i) => standardDay(i, i <= 4 ? WORK_DAY_KIND_CODE.FULL : WORK_DAY_KIND_CODE.OFF))
    case 'sixDays':
      return filled.map((_, i) => standardDay(i, i <= 5 ? WORK_DAY_KIND_CODE.FULL : WORK_DAY_KIND_CODE.OFF))
    case 'saturdayMorning':
      return filled.map((d, i) => (i === 5 ? standardDay(i, WORK_DAY_KIND_CODE.MORNING) : d))
  }
}

/** Chép giờ của T2 xuống T3–T6; T7 và CN là ngày đặc thù nên cố ý KHÔNG đè. */
export function copyMondayToWeekdays(week: WorkScheduleDay[]): WorkScheduleDay[] {
  const filled = fillWeek(week)
  return filled.map((d, i) => (i >= 1 && i <= 4 ? { ...filled[0], weekday: i } : d))
}
