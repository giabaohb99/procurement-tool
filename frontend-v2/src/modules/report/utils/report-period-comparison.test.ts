import { describe, expect, it } from 'vitest'

import {
  buildMonthComparison,
  comparableMonthCount,
  maskFutureMonths,
  percentChange,
  ratePercent,
  sumFirstMonths,
} from './report-period-comparison'

describe('buildMonthComparison', () => {
  it('always returns 12 months, zero-filling months without spend', () => {
    const points = buildMonthComparison(2026, [{ month: '2026-03', amount: 5 }], [])
    expect(points).toHaveLength(12)
    expect(points.map((p) => p.label)[0]).toBe('T1')
    expect(points[2]).toEqual({ label: 'T3', current: 5, previous: 0 })
    expect(points[0]).toEqual({ label: 'T1', current: 0, previous: 0 })
  })

  it('puts last year on the same month slot as this year', () => {
    const points = buildMonthComparison(
      2026,
      [{ month: '2026-07', amount: 10 }],
      [{ month: '2025-07', amount: 4 }],
    )
    expect(points[6]).toEqual({ label: 'T7', current: 10, previous: 4 })
  })

  //  Backend lọc công nợ theo cột `period`, không theo chuỗi tháng — điểm của
  //  năm khác lọt vào được. Cộng nhầm là số tháng 1 năm nay gánh cả tháng 1 năm trước.
  it('ignores points from another year and malformed months instead of summing them in', () => {
    const points = buildMonthComparison(
      2026,
      [
        { month: '2025-01', amount: 99 },
        { month: '2026-13', amount: 99 },
        { month: '', amount: 99 },
        { month: '2026-01', amount: 1 },
      ],
      [{ month: '2026-01', amount: 99 }],
    )
    expect(points[0]).toEqual({ label: 'T1', current: 1, previous: 0 })
    expect(points.reduce((s, p) => s + p.current + p.previous, 0)).toBe(1)
  })

  it('adds up duplicate points of the same month', () => {
    const points = buildMonthComparison(
      2026,
      [
        { month: '2026-02', amount: 2 },
        { month: '2026-02', amount: 3 },
      ],
      [],
    )
    expect(points[1].current).toBe(5)
  })
})

describe('comparableMonthCount', () => {
  it('compares the running year only up to the current month (same period, not full year)', () => {
    expect(comparableMonthCount(2026, new Date(2026, 8, 26))).toBe(9)
    expect(comparableMonthCount(2026, new Date(2026, 0, 1))).toBe(1)
  })

  it('uses all 12 months for past years and none for future years', () => {
    expect(comparableMonthCount(2025, new Date(2026, 8, 26))).toBe(12)
    expect(comparableMonthCount(2027, new Date(2026, 8, 26))).toBe(0)
  })
})

describe('sumFirstMonths / maskFutureMonths', () => {
  const points = buildMonthComparison(
    2026,
    Array.from({ length: 12 }, (_, i) => ({ month: `2026-${String(i + 1).padStart(2, '0')}`, amount: 1 })),
    Array.from({ length: 12 }, (_, i) => ({ month: `2025-${String(i + 1).padStart(2, '0')}`, amount: 2 })),
  )

  it('sums the same window on both years', () => {
    expect(sumFirstMonths(points, 9)).toEqual({ current: 9, previous: 18 })
  })

  it('treats zero or negative windows as empty rather than slicing from the end', () => {
    expect(sumFirstMonths(points, 0)).toEqual({ current: 0, previous: 0 })
    expect(sumFirstMonths(points, -3)).toEqual({ current: 0, previous: 0 })
  })

  it('blanks this year after the window but keeps last year whole', () => {
    const masked = maskFutureMonths(points, 9)
    expect(masked[8].current).toBe(1)
    expect(masked[9].current).toBeNull()
    expect(masked[11].previous).toBe(2)
  })
})

describe('percentChange', () => {
  it('returns relative change against the previous period', () => {
    expect(percentChange(150, 100)).toBe(50)
    expect(percentChange(50, 100)).toBe(-50)
    expect(percentChange(0, 100)).toBe(-100)
  })

  it('returns null when there is no previous period to compare against', () => {
    expect(percentChange(100, 0)).toBeNull()
    expect(percentChange(0, 0)).toBeNull()
    expect(percentChange(Number.NaN, 10)).toBeNull()
    expect(percentChange(10, Number.POSITIVE_INFINITY)).toBeNull()
  })

  it('keeps the sign right when the previous period is negative (refunds)', () => {
    expect(percentChange(-50, -100)).toBe(50)
  })
})

describe('ratePercent', () => {
  it('returns null for an empty sample instead of 0% or NaN', () => {
    expect(ratePercent(0, 0)).toBeNull()
    expect(ratePercent(3, -1)).toBeNull()
  })

  it('computes the share', () => {
    expect(ratePercent(3, 4)).toBe(75)
  })
})
