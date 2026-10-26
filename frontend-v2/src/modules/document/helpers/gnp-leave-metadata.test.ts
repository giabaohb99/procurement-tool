import { describe, expect, it } from 'vitest'

import { formatGnpLeavePeriod, gnpLeavePeriodsOf, leaveExtraOf } from './gnp-leave-metadata'

/**
 * Bản kê khoảng ngày trên giấy GNP (duoc-CR-683 M4). Giấy hệ sinh cho đơn 27/10 + 03/11→07/11
 * từng chỉ hiện «27/10/2026 → 07/11/2026, 5.5 ngày» — đọc thành 12 ngày nghỉ liền.
 */

const twoPeriods = [
  { from_date: '2026-10-27', from_session: 'full', to_date: '2026-10-27', to_session: 'full', days: 1 },
  { from_date: '2026-11-03', from_session: 'afternoon', to_date: '2026-11-07', to_session: 'full', days: 4.5 },
]

describe('leaveExtraOf', () => {
  it('keeps every metadata key the form has no field for, and only those', () => {
    const extra = leaveExtraOf({
      from_date: '2026-10-27',
      total_days: 5.5,
      reason: 'Việc nhà',
      leave_periods: twoPeriods,
      leave_lines: [{ code: 'annual', days: 5.5 }],
    })
    expect(extra).toEqual({ leave_periods: twoPeriods, leave_lines: [{ code: 'annual', days: 5.5 }] })
  })

  it('survives a document with no metadata at all', () => {
    expect(leaveExtraOf(null)).toEqual({})
    expect(leaveExtraOf(undefined)).toEqual({})
  })
})

describe('gnpLeavePeriodsOf', () => {
  it('returns the periods of a multi-period GNP', () => {
    expect(gnpLeavePeriodsOf({ leave_periods: twoPeriods })).toEqual(twoPeriods)
  })

  it('returns nothing for one period — the two date fields already say it', () => {
    expect(gnpLeavePeriodsOf({ leave_periods: [twoPeriods[0]] })).toEqual([])
  })

  it('ignores junk instead of crashing the document screen', () => {
    expect(gnpLeavePeriodsOf(undefined)).toEqual([])
    expect(gnpLeavePeriodsOf({ leave_periods: 'oops' })).toEqual([])
    //  Phần tử hỏng bị bỏ; còn lại một khoảng thì cũng không kê.
    expect(gnpLeavePeriodsOf({ leave_periods: [null, 7, { from_date: 1 }, twoPeriods[0]] })).toEqual([])
    const kept = gnpLeavePeriodsOf({ leave_periods: [twoPeriods[0], { from_date: '2026-11-03', to_date: '2026-11-04' }] })
    expect(kept[1]).toEqual({
      from_date: '2026-11-03',
      from_session: 'full',
      to_date: '2026-11-04',
      to_session: 'full',
      days: 0,
    })
  })
})

describe('formatGnpLeavePeriod', () => {
  it('a one-day period shows the date, the session and the day count', () => {
    expect(formatGnpLeavePeriod(twoPeriods[0])).toBe('27/10/2026 (cả ngày) · 1 ngày')
  })

  it('a multi-day period shows both ends with their sessions', () => {
    expect(formatGnpLeavePeriod(twoPeriods[1])).toBe(
      '03/11/2026 (chiều) → 07/11/2026 (cả ngày) · 4.5 ngày',
    )
  })

  it('a morning-only day reads «sáng», an unknown code falls back to «cả ngày»', () => {
    const morning = { ...twoPeriods[0], from_session: 'morning', to_session: 'morning', days: 0.5 }
    expect(formatGnpLeavePeriod(morning)).toBe('27/10/2026 (sáng) · 0.5 ngày')
    const odd = { ...twoPeriods[0], from_session: 'hourly??', to_session: 'hourly??' }
    expect(formatGnpLeavePeriod(odd)).toBe('27/10/2026 (cả ngày) · 1 ngày')
  })
})
