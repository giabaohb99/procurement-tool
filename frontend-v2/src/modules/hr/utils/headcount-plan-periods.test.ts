import { describe, expect, it } from 'vitest'

import { PLAN_PERIOD_TYPE, PLAN_PERIOD_TYPE_CODE } from '@/shared/constants/statuses'
import {
  buildPeriodNoOptions,
  buildSubPeriods,
  clampPeriodNo,
  formatPeriodLabel,
  listPeriodMonths,
  resizeHeadcounts,
} from './headcount-plan-periods'

const { YEAR, HALF, QUARTER, MONTH } = PLAN_PERIOD_TYPE_CODE

describe('sub-periods per period type (doc 06 §3)', () => {
  it('splits a year into four quarters covering all twelve months', () => {
    const p = buildSubPeriods(YEAR, 1)
    expect(p.map((x) => x.label)).toEqual(['Q1', 'Q2', 'Q3', 'Q4'])
    expect(p.flatMap((x) => x.months)).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
  })

  it('splits H2 into Q3 and Q4, not Q1 and Q2', () => {
    expect(buildSubPeriods(HALF, 2).map((x) => x.label)).toEqual(['Q3', 'Q4'])
    expect(listPeriodMonths(HALF, 2)).toEqual([7, 8, 9, 10, 11, 12])
  })

  it('shows three month columns for a quarter', () => {
    expect(buildSubPeriods(QUARTER, 3).map((x) => x.label)).toEqual(['T7', 'T8', 'T9'])
  })

  it('has one column for a month', () => {
    expect(buildSubPeriods(MONTH, 12)).toEqual([{ key: 'M12', label: 'T12', months: [12] }])
  })

  it('clamps an out-of-range period number instead of producing an empty or month-13 column', () => {
    expect(listPeriodMonths(QUARTER, 7)).toEqual([10, 11, 12])
    expect(listPeriodMonths(MONTH, 0)).toEqual([1])
    expect(listPeriodMonths(MONTH, -5)).toEqual([1])
    expect(listPeriodMonths(MONTH, Number.NaN)).toEqual([1])
    expect(clampPeriodNo(YEAR, 4)).toBe(1)
  })

  it('treats an unknown period type as a year rather than crashing', () => {
    expect(buildSubPeriods(99, 1)).toHaveLength(4)
  })

  it('offers exactly as many period numbers as the type allows, for every generated period type', () => {
    const counts = PLAN_PERIOD_TYPE.map((o) => buildPeriodNoOptions(Number(o.value)).length)
    expect(counts).toEqual([1, 2, 4, 12])
  })
})

describe('period label', () => {
  it('pads the month and prefixes half/quarter the way people say it', () => {
    expect(formatPeriodLabel(YEAR, 1, 2026)).toBe('2026')
    expect(formatPeriodLabel(HALF, 1, 2026)).toBe('H1-2026')
    expect(formatPeriodLabel(QUARTER, 4, 2027)).toBe('Q4-2027')
    expect(formatPeriodLabel(MONTH, 7, 2026)).toBe('07/2026')
  })
})

describe('resizing headcounts when the period type changes', () => {
  it('keeps values when the length is unchanged (Q1 → Q2 of the same type)', () => {
    expect(resizeHeadcounts([1, 2, 3], 3)).toEqual([1, 2, 3])
  })

  it('fills every new column with the old END headcount instead of cutting by index', () => {
    //  Năm [0,1,1,5] → Quý: cắt theo chỉ số ra [0,1,1] là mất con số đích 5.
    expect(resizeHeadcounts([0, 1, 1, 5], 3)).toEqual([5, 5, 5])
    expect(resizeHeadcounts([4], 4)).toEqual([4, 4, 4, 4])
  })

  it('never produces negatives, fractions or NaN, and handles empty input', () => {
    expect(resizeHeadcounts([-3], 2)).toEqual([0, 0])
    expect(resizeHeadcounts([2.7], 2)).toEqual([2, 2])
    expect(resizeHeadcounts([Number.NaN], 2)).toEqual([0, 0])
    expect(resizeHeadcounts([], 3)).toEqual([0, 0, 0])
    expect(resizeHeadcounts([1, 2], 0)).toEqual([])
  })
})
