import { describe, expect, it } from 'vitest'

import { WORK_DAY_KIND_CODE } from '../types/work-schedule'
import { buildDefaultWeek } from './work-schedule-week'
import { isChosenId, validateWeekDays } from './work-schedule-validation'

describe('isChosenId', () => {
  it('accepts positive integers, numeric strings included', () => {
    expect(isChosenId(3)).toBe(true)
    expect(isChosenId('12')).toBe(true)
  })

  it('rejects 0, negatives, fractions, NaN, empty and non-numeric input', () => {
    for (const bad of [0, -1, 1.5, Number.NaN, '', null, undefined, 'abc', {}, []]) {
      expect(isChosenId(bad)).toBe(false)
    }
  })
})

describe('validateWeekDays', () => {
  it('default week is valid; empty / garbage input becomes 7 OFF days and is valid', () => {
    expect(validateWeekDays(buildDefaultWeek())).toBe(true)
    for (const bad of [[], null, undefined, 'x']) expect(validateWeekDays(bad)).toBe(true)
  })

  it('names the weekday whose in/out time is missing', () => {
    const week = buildDefaultWeek()
    week[2] = { ...week[2], start_time: null }
    expect(validateWeekDays(week)).toBe('T4: nhập đủ giờ vào và giờ ra.')
  })

  it('rejects end <= start (equal and reversed) on any working kind', () => {
    for (const [start, end] of [['17:00', '08:00'], ['08:00', '08:00']]) {
      const week = buildDefaultWeek()
      week[0] = { ...week[0], day_kind: WORK_DAY_KIND_CODE.MORNING, start_time: start, end_time: end, lunch_start: null, lunch_end: null }
      expect(validateWeekDays(week)).toBe('T2: giờ ra phải sau giờ vào.')
    }
  })

  it('rejects a half-filled lunch pair on a FULL day, accepts both empty', () => {
    const week = buildDefaultWeek()
    week[1] = { ...week[1], lunch_end: null }
    expect(validateWeekDays(week)).toMatch(/^T3: nhập đủ cả giờ nghỉ trưa/)
    week[1] = { ...week[1], lunch_start: null, lunch_end: null }
    expect(validateWeekDays(week)).toBe(true)
  })

  it('an OFF day with stray hours is not an error (they are cleared on kind change)', () => {
    const week = buildDefaultWeek()
    week[6] = { ...week[6], start_time: '25:99' }
    expect(validateWeekDays(week)).toBe(true)
  })
})
