import { describe, expect, it } from 'vitest'

import { formatShiftDayLabel, weekdayOf } from './work-shift-date'

describe('work-shift dates', () => {
  it('reads the weekday from the calendar date, Monday = 0, Sunday = 6', () => {
    expect(weekdayOf('2026-11-16')).toBe(0)
    expect(weekdayOf('2026-11-22')).toBe(6)
    expect(weekdayOf('garbage')).toBe(-1)
  })

  it('formats the full Vietnamese weekday + dd/mm/yyyy, leaving broken input untouched', () => {
    expect(formatShiftDayLabel('2026-11-19')).toBe('Thứ Năm, 19/11/2026')
    expect(formatShiftDayLabel('2026-11-22')).toBe('Chủ nhật, 22/11/2026')
    expect(formatShiftDayLabel('')).toBe('')
  })
})
