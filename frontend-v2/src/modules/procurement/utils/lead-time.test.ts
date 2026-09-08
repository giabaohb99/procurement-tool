import { describe, expect, it } from 'vitest'

import {
  addDays,
  buildStdDaysMap,
  calcRegulatedDate,
  DEFAULT_STD_DAYS,
  findStdDays,
  normalizeGroupName,
} from './lead-time'

describe('normalizeGroupName', () => {
  it('collapses case and repeated spaces so catalog lookups still match', () => {
    expect(normalizeGroupName('  Nhãn   Thùng ')).toBe('nhãn thùng')
    expect(normalizeGroupName('Nhãn thùng')).toBe(normalizeGroupName('NHÃN THÙNG'))
  })

  it('turns missing names into an empty key instead of crashing', () => {
    expect(normalizeGroupName(null)).toBe('')
    expect(normalizeGroupName(undefined)).toBe('')
    expect(normalizeGroupName('   ')).toBe('')
  })
})

describe('buildStdDaysMap', () => {
  it('always keeps the longer "out of stock" lead time', () => {
    const map = buildStdDaysMap([{ name: 'Bao bì', std_days: '5', std_days_unavail: '20' }])
    expect(findStdDays(map, 'Bao bì')).toBe(20)
  })

  it('falls back to the in-stock lead time, then to the default', () => {
    const map = buildStdDaysMap([
      { name: 'Bao bì', std_days: '7', std_days_unavail: '' },
      { name: 'Nguyên liệu', std_days: null, std_days_unavail: null },
    ])
    expect(findStdDays(map, 'Bao bì')).toBe(7)
    expect(findStdDays(map, 'Nguyên liệu')).toBe(DEFAULT_STD_DAYS)
  })

  //  Danh mục cũ có phiếu gõ "15 ngày" vào ô số — cắt phần chữ chứ đừng ra 0.
  it('reads a number out of a value that carries text', () => {
    const map = buildStdDaysMap([{ name: 'Bao bì', std_days_unavail: '30 ngày' }])
    expect(findStdDays(map, 'Bao bì')).toBe(30)
  })

  it('survives an empty or missing catalog', () => {
    expect(buildStdDaysMap([])).toEqual({})
    expect(buildStdDaysMap(undefined)).toEqual({})
  })
})

describe('findStdDays', () => {
  it('gives the default for an unknown or blank group', () => {
    const map = buildStdDaysMap([{ name: 'Bao bì', std_days_unavail: '20' }])
    expect(findStdDays(map, 'Không có trong danh mục')).toBe(DEFAULT_STD_DAYS)
    expect(findStdDays(map, '')).toBe(DEFAULT_STD_DAYS)
  })
})

describe('addDays', () => {
  it('adds in UTC so the result never slips a day in Asia/Ho_Chi_Minh', () => {
    expect(addDays('2026-08-31', 1)).toBe('2026-09-01')
    expect(addDays('2026-12-31', 1)).toBe('2027-01-01')
    expect(addDays('2024-02-28', 1)).toBe('2024-02-29')
  })

  it('ignores the time part of an ISO datetime', () => {
    expect(addDays('2026-08-31T23:30:00Z', 1)).toBe('2026-09-01')
  })

  it('returns blank when there is no usable base date or no days to add', () => {
    expect(addDays('', 15)).toBe('')
    expect(addDays('31/08/2026', 15)).toBe('')
    expect(addDays('2026-08-31', 0)).toBe('')
    expect(addDays('2026-08-31', -5)).toBe('')
  })
})

describe('calcRegulatedDate', () => {
  it('is order date + the group lead time', () => {
    const map = buildStdDaysMap([{ name: 'Bao bì', std_days_unavail: '20' }])
    expect(calcRegulatedDate(map, 'bao bì', '2026-08-31')).toBe('2026-09-20')
  })

  it('still uses the default lead time for a group outside the catalog', () => {
    expect(calcRegulatedDate({}, 'Lạ hoắc', '2026-08-31')).toBe('2026-09-15')
  })

  it('leaves the date blank when the order has no order date yet', () => {
    const map = buildStdDaysMap([{ name: 'Bao bì', std_days_unavail: '20' }])
    expect(calcRegulatedDate(map, 'Bao bì', '')).toBe('')
  })
})
