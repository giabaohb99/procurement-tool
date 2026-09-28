import { describe, expect, it } from 'vitest'

import {
  DEFAULT_REPORT_PRESET,
  isReportPresetKey,
  REPORT_PRESETS,
  resolveLocalPresetRange,
} from './report-period-presets'

describe('REPORT_PRESETS', () => {
  it('has exactly the 10 keys the backend `preset` parameter accepts, in menu order', () => {
    expect(REPORT_PRESETS.map((p) => p.key)).toEqual([
      'today',
      'yesterday',
      'last_7_days',
      'last_30_days',
      'this_month',
      'last_month',
      'this_quarter',
      'this_year',
      'last_year',
      'custom',
    ])
  })

  it('defaults to "this_month" (Q0.1, chốt 28/09/2026 — not last_30_days)', () => {
    expect(DEFAULT_REPORT_PRESET).toBe('this_month')
  })
})

describe('isReportPresetKey', () => {
  it('accepts only the declared keys, rejects garbage and null', () => {
    expect(isReportPresetKey('this_month')).toBe(true)
    expect(isReportPresetKey('this-month')).toBe(false)
    expect(isReportPresetKey('')).toBe(false)
    expect(isReportPresetKey(null)).toBe(false)
  })
})

describe('resolveLocalPresetRange', () => {
  it('resolves "this_year" to Jan 1 – Dec 31 of the current year', () => {
    expect(resolveLocalPresetRange('this_year', new Date(2026, 11, 15))).toEqual([
      '2026-01-01',
      '2026-12-31',
    ])
  })

  it('resolves "this_month" (and "custom", its seed) to the 1st – last day of the current month', () => {
    expect(resolveLocalPresetRange('this_month', new Date(2026, 8, 28))).toEqual([
      '2026-09-01',
      '2026-09-30',
    ])
    expect(resolveLocalPresetRange('custom', new Date(2026, 8, 28))).toEqual([
      '2026-09-01',
      '2026-09-30',
    ])
  })

  it('resolves "this_quarter" to calendar quarter boundaries (Q4 = Oct–Dec)', () => {
    expect(resolveLocalPresetRange('this_quarter', new Date(2026, 10, 5))).toEqual([
      '2026-10-01',
      '2026-12-31',
    ])
  })

  it('crosses the year boundary for "last_month" when run in January', () => {
    expect(resolveLocalPresetRange('last_month', new Date(2026, 0, 15))).toEqual([
      '2025-12-01',
      '2025-12-31',
    ])
  })

  it('"yesterday" crosses day 1 of the month, including leap-year Feb 29', () => {
    expect(resolveLocalPresetRange('yesterday', new Date(2026, 2, 1))).toEqual([
      '2026-02-28',
      '2026-02-28',
    ])
    //  2028 is a leap year — March 1 → Feb 29, not Feb 28.
    expect(resolveLocalPresetRange('yesterday', new Date(2028, 2, 1))).toEqual([
      '2028-02-29',
      '2028-02-29',
    ])
  })

  it('"last_year" is fully independent of the current month', () => {
    expect(resolveLocalPresetRange('last_year', new Date(2026, 0, 1))).toEqual([
      '2025-01-01',
      '2025-12-31',
    ])
  })
})
