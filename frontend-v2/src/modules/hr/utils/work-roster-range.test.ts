import { describe, expect, it } from 'vitest'

import { parseISODate, parseRosterMode, rosterRange, todayInVietnamISO } from './work-roster-range'

describe('rosterRange', () => {
  it('starts the week on Monday even when the anchor is a Sunday', () => {
    //  05/10/2026 là Thứ Hai; 11/10/2026 là Chủ nhật — vẫn thuộc tuần 05/10.
    expect(rosterRange(new Date(2026, 9, 11), 'week')).toEqual({
      from: '2026-10-05',
      to: '2026-10-11',
    })
    expect(rosterRange(new Date(2026, 9, 5), 'week')).toEqual({
      from: '2026-10-05',
      to: '2026-10-11',
    })
  })

  it('keeps 7 days when a week spans months and years', () => {
    expect(rosterRange(new Date(2026, 11, 31), 'week')).toEqual({
      from: '2026-12-28',
      to: '2027-01-03',
    })
  })

  it('asks the month from the 1st to the last day, not a 42-cell grid', () => {
    expect(rosterRange(new Date(2026, 9, 17), 'month')).toEqual({
      from: '2026-10-01',
      to: '2026-10-31',
    })
  })

  it('handles February in leap and non-leap years', () => {
    expect(rosterRange(new Date(2028, 1, 10), 'month').to).toBe('2028-02-29')
    expect(rosterRange(new Date(2027, 1, 10), 'month').to).toBe('2027-02-28')
  })

  it('never exceeds the backend 42-day cap', () => {
    for (let m = 0; m < 12; m++) {
      const { from, to } = rosterRange(new Date(2026, m, 15), 'month')
      const span = (Date.parse(to) - Date.parse(from)) / 86_400_000 + 1
      expect(span).toBeLessThanOrEqual(42)
    }
  })
})

describe('parseISODate', () => {
  it('accepts a valid date', () => {
    expect(parseISODate('2026-10-05')?.getDate()).toBe(5)
  })

  it.each(['', 'abc', '2026-13-01', '2026-02-31', '2026-1-5', '1999-12-31', '2101-01-01', "2026-10-05'--"])(
    'từ chối %j',
    (value) => {
      expect(parseISODate(value)).toBeNull()
    },
  )
})

describe('parseRosterMode', () => {
  it('accepts only month and falls back to week for anything else', () => {
    expect(parseRosterMode('month')).toBe('month')
    expect(parseRosterMode('day')).toBe('week')
    expect(parseRosterMode('')).toBe('week')
    expect(parseRosterMode(null)).toBe('week')
    expect(parseRosterMode(undefined)).toBe('week')
  })
})

describe('todayInVietnamISO', () => {
  //  Lỗi cũ: «hôm nay» lấy theo múi giờ máy — máy giờ UTC lúc 00:30 sáng VN vẫn hiện hôm qua.
  it('reads the Vietnam calendar day across the UTC midnight boundary', () => {
    expect(todayInVietnamISO(new Date('2026-10-05T16:59:59Z'))).toBe('2026-10-05')
    expect(todayInVietnamISO(new Date('2026-10-05T17:00:00Z'))).toBe('2026-10-06')
  })

  it('rolls over month and year ends and handles a leap day', () => {
    expect(todayInVietnamISO(new Date('2026-12-31T20:00:00Z'))).toBe('2027-01-01')
    expect(todayInVietnamISO(new Date('2028-02-28T18:00:00Z'))).toBe('2028-02-29')
  })

  it('always returns a string parseISODate accepts', () => {
    expect(parseISODate(todayInVietnamISO())).not.toBeNull()
  })
})
