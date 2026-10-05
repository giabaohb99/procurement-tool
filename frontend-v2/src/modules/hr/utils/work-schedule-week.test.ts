import { describe, expect, it } from 'vitest'

import { WORK_DAY_KIND, WORK_SCHEDULE_LEVEL } from '@/shared/constants/statuses'
import {
  WORK_DAY_KIND_CODE,
  WORK_SCHEDULE_LEVEL_CODE,
  type WorkScheduleDay,
} from '../types/work-schedule'
import {
  applyWeekPreset,
  buildDefaultWeek,
  copyMondayToWeekdays,
  dayCredit,
  fillWeek,
  formatWorkdays,
  normalizeDayOnKindChange,
  sumWeeklyWorkdays,
  toTimeInput,
} from './work-schedule-week'

const OFF = WORK_DAY_KIND_CODE.OFF
const FULL = WORK_DAY_KIND_CODE.FULL
const MORNING = WORK_DAY_KIND_CODE.MORNING

function day(weekday: number, kind: number, start: string | null = null, end: string | null = null): WorkScheduleDay {
  return { weekday, day_kind: kind, start_time: start, end_time: end, lunch_start: null, lunch_end: null }
}

describe('hằng *_CODE khớp bộ mã sinh từ backend', () => {
  it('WORK_DAY_KIND_CODE trùng giá trị trong statuses.ts (backend đổi số thì test đỏ)', () => {
    const byLabel = Object.fromEntries(WORK_DAY_KIND.map((o) => [o.label, Number(o.value)]))
    expect(byLabel['Nghỉ']).toBe(WORK_DAY_KIND_CODE.OFF)
    expect(byLabel['Cả ngày']).toBe(WORK_DAY_KIND_CODE.FULL)
    expect(byLabel['Buổi sáng']).toBe(WORK_DAY_KIND_CODE.MORNING)
    expect(byLabel['Buổi chiều']).toBe(WORK_DAY_KIND_CODE.AFTERNOON)
    expect(WORK_DAY_KIND).toHaveLength(Object.keys(WORK_DAY_KIND_CODE).length)
  })

  it('WORK_SCHEDULE_LEVEL_CODE trùng giá trị trong statuses.ts', () => {
    const byLabel = Object.fromEntries(WORK_SCHEDULE_LEVEL.map((o) => [o.label, Number(o.value)]))
    expect(byLabel['Toàn hệ thống']).toBe(WORK_SCHEDULE_LEVEL_CODE.SYSTEM)
    expect(byLabel['Pháp nhân']).toBe(WORK_SCHEDULE_LEVEL_CODE.COMPANY)
    expect(byLabel['Phòng ban']).toBe(WORK_SCHEDULE_LEVEL_CODE.DEPARTMENT)
    expect(byLabel['Nhân sự']).toBe(WORK_SCHEDULE_LEVEL_CODE.EMPLOYEE)
    expect(WORK_SCHEDULE_LEVEL).toHaveLength(Object.keys(WORK_SCHEDULE_LEVEL_CODE).length)
  })
})

describe('toTimeInput', () => {
  it('cắt giây của giờ backend và đệm số 0', () => {
    expect(toTimeInput('08:00:00')).toBe('08:00')
    expect(toTimeInput('8:00')).toBe('08:00')
  })

  it('trả chuỗi rỗng cho null, rỗng, kiểu lạ và giờ ngoài dải, không ném lỗi', () => {
    for (const bad of [null, undefined, '', '   ', 'abc', '24:00', '12:60', 8, {}]) {
      expect(toTimeInput(bad)).toBe('')
    }
  })
})

describe('sumWeeklyWorkdays / dayCredit', () => {
  it('mẫu mặc định T2–T7 cả ngày = 6 công', () => {
    expect(sumWeeklyWorkdays(buildDefaultWeek())).toBe(6)
  })

  it('T7 chỉ buổi sáng thì tuần là 5,5 công', () => {
    const week = buildDefaultWeek()
    week[5] = day(5, MORNING, '08:00', '12:00')
    expect(sumWeeklyWorkdays(week)).toBe(5.5)
    expect(formatWorkdays(5.5)).toBe('5,5')
  })

  it('toàn nghỉ, mảng rỗng, không phải mảng đều ra 0 và không nổ', () => {
    expect(sumWeeklyWorkdays(Array.from({ length: 7 }, (_, i) => day(i, OFF)))).toBe(0)
    expect(sumWeeklyWorkdays([])).toBe(0)
    expect(sumWeeklyWorkdays(null)).toBe(0)
    expect(sumWeeklyWorkdays('x')).toBe(0)
  })

  it('bảy ngày cả ngày = 7; loại ngày lạ không có công', () => {
    expect(sumWeeklyWorkdays(Array.from({ length: 7 }, (_, i) => day(i, FULL, '08:00', '17:00')))).toBe(7)
    expect(dayCredit(99)).toBe(0)
    expect(dayCredit(0)).toBe(0)
  })

  it('thứ trùng không bị đếm đôi và thứ ngoài 0..6 bị bỏ', () => {
    const week = [day(0, FULL), day(0, FULL), day(9, FULL), day(-1, FULL)]
    expect(sumWeeklyWorkdays(week)).toBe(1)
  })
})

describe('fillWeek', () => {
  it('luôn trả đúng 7 hàng theo thứ tự T2..CN dù đầu vào xáo trộn hoặc thiếu', () => {
    const result = fillWeek([day(6, OFF), day(0, FULL, '08:00:00', '17:00:00')])
    expect(result.map((d) => d.weekday)).toEqual([0, 1, 2, 3, 4, 5, 6])
    expect(result[0].start_time).toBe('08:00')
    expect(result[3].day_kind).toBe(OFF)
  })

  it('đầu vào hỏng (null, phần tử null) không làm nổ', () => {
    expect(fillWeek(null)).toHaveLength(7)
    expect(fillWeek([null, undefined, 5])).toHaveLength(7)
  })
})

describe('normalizeDayOnKindChange', () => {
  const AFTERNOON = WORK_DAY_KIND_CODE.AFTERNOON
  const KINDS = [OFF, FULL, MORNING, AFTERNOON]
  /** Giờ chuẩn của từng loại: [giờ vào, giờ ra, trưa từ, trưa đến]. */
  const STANDARD: Record<number, (string | null)[]> = {
    [OFF]: [null, null, null, null],
    [FULL]: ['08:00', '17:00', '12:00', '13:00'],
    [MORNING]: ['08:00', '12:00', null, null],
    [AFTERNOON]: ['13:00', '17:00', null, null],
  }
  const times = (d: WorkScheduleDay) => [d.start_time, d.end_time, d.lunch_start, d.lunch_end]

  /** Một ngày ĐÚNG loại `kind` với giờ chuẩn, để thử đổi sang loại khác. */
  function standardDay(kind: number): WorkScheduleDay {
    const [start, end, lunchStart, lunchEnd] = STANDARD[kind]
    return { weekday: 2, day_kind: kind, start_time: start, end_time: end, lunch_start: lunchStart, lunch_end: lunchEnd }
  }

  // Regression: Cả ngày 08–17 đổi sang Buổi sáng từng GIỮ giờ ra 17:00 -> «sáng 08–17»,
  // nghỉ phép theo giờ tính sai im lặng. Kiểm cả bốn ô cho MỌI cặp loại khác nhau.
  for (const from of KINDS) {
    for (const to of KINDS) {
      if (from === to) continue
      it(`kind ${from} -> ${to} resets all four time fields to the target standard`, () => {
        const result = normalizeDayOnKindChange(standardDay(from), to)
        expect(result.day_kind).toBe(to)
        expect(result.weekday).toBe(2)
        expect(times(result)).toEqual(STANDARD[to])
      })
    }
  }

  it('resets even when the old day carries custom hours (07:30–16:30 FULL -> MORNING)', () => {
    const custom = { ...day(1, FULL, '07:30', '16:30'), lunch_start: '11:30', lunch_end: '12:30' }
    expect(times(normalizeDayOnKindChange(custom, MORNING))).toEqual(['08:00', '12:00', null, null])
    expect(times(normalizeDayOnKindChange(custom, OFF))).toEqual([null, null, null, null])
  })

  it('picking the SAME kind again keeps the hours the user edited (end_time included)', () => {
    const custom = { ...day(1, FULL, '07:30', '16:30'), lunch_start: '11:30', lunch_end: '12:30' }
    expect(times(normalizeDayOnKindChange(custom, FULL))).toEqual(['07:30', '16:30', '11:30', '12:30'])
    const am = day(5, MORNING, '07:00', '11:00')
    expect(times(normalizeDayOnKindChange(am, MORNING))).toEqual(['07:00', '11:00', null, null])
  })

  it('an unknown target kind is treated like OFF (no stray hours reach the payload)', () => {
    expect(times(normalizeDayOnKindChange(standardDay(FULL), 99))).toEqual([null, null, null, null])
  })

  it('does not mutate the input day', () => {
    const original = day(0, FULL, '08:00', '17:00')
    normalizeDayOnKindChange(original, OFF)
    expect(original.start_time).toBe('08:00')
    expect(original.end_time).toBe('17:00')
  })
})

describe('applyWeekPreset', () => {
  it('office = T2–T6 full day on standard hours, T7 and CN off, total 5', () => {
    const week = applyWeekPreset(buildDefaultWeek(), 'office')
    expect(week.map((d) => d.day_kind)).toEqual([FULL, FULL, FULL, FULL, FULL, OFF, OFF])
    expect(week[0]).toMatchObject({ start_time: '08:00', end_time: '17:00', lunch_start: '12:00', lunch_end: '13:00' })
    expect(week[5]).toMatchObject({ start_time: null, end_time: null, lunch_start: null, lunch_end: null })
    expect(sumWeeklyWorkdays(week)).toBe(5)
  })

  it('sixDays = T2–T7 full day, CN off, total 6, and also resets hand-edited hours', () => {
    const edited = buildDefaultWeek().map((d) => ({ ...d, start_time: d.start_time ? '07:00' : null }))
    const week = applyWeekPreset(edited, 'sixDays')
    expect(week[0].start_time).toBe('08:00')
    expect(week[5].day_kind).toBe(WORK_DAY_KIND_CODE.FULL)
    expect(week[6].day_kind).toBe(WORK_DAY_KIND_CODE.OFF)
    expect(sumWeeklyWorkdays(week)).toBe(6)
  })

  it('saturdayMorning only touches T7 and keeps every other day as it was', () => {
    const base = buildDefaultWeek()
    base[0] = { ...base[0], start_time: '07:30' }
    const week = applyWeekPreset(base, 'saturdayMorning')
    expect(week[5]).toMatchObject({ day_kind: WORK_DAY_KIND_CODE.MORNING, start_time: '08:00', end_time: '12:00', lunch_start: null })
    expect(week[0].start_time).toBe('07:30')
    expect(sumWeeklyWorkdays(week)).toBe(5.5)
  })

  it('survives a missing / garbage week by filling seven rows', () => {
    for (const bad of [undefined, null, 'oops', []]) {
      expect(applyWeekPreset(bad as never, 'office')).toHaveLength(7)
    }
  })
})

describe('copyMondayToWeekdays', () => {
  it('copies T2 into T3–T6 with their own weekday and leaves T7 and CN alone', () => {
    const base = buildDefaultWeek()
    base[0] = { ...base[0], start_time: '07:30' }
    const week = copyMondayToWeekdays(base)
    for (const i of [1, 2, 3, 4]) expect(week[i]).toMatchObject({ weekday: i, start_time: '07:30' })
    expect(week[5]).toEqual(base[5])
    expect(week[6]).toEqual(base[6])
  })
})
