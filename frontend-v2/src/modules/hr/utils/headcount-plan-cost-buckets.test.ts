import { describe, expect, it } from 'vitest'

import { COST_CALC_METHOD, COST_CALC_METHOD_CODE } from '@/shared/constants/statuses'
import { bucketOfMethod, buildCostBucketRows, sumLineHeadcounts } from './headcount-plan-cost-buckets'

const M = COST_CALC_METHOD_CODE
const row = (code: string, values: number[]) => ({ code, name: code, values, total: values.reduce((a, b) => a + b, 0) })

const ITEMS = [
  { code: 'LUONG', calc_method: M.PER_HEAD_MONTH },
  { code: 'PHU_CAP', calc_method: M.PER_HEAD_MONTH },
  { code: 'BH', calc_method: M.PERCENT_OF },
  { code: 'T13', calc_method: M.MONTHS_OF },
  { code: 'QUA', calc_method: M.PER_HEAD_ONCE },
  { code: 'DL', calc_method: M.LUMP_SUM },
]

describe('three money rows of the Tổng table', () => {
  it('maps every generated method onto one of the three rows — a new backend code must not vanish', () => {
    for (const o of COST_CALC_METHOD) expect(['salary', 'insurance', 'bonus']).toContain(bucketOfMethod(Number(o.value)))
    expect(bucketOfMethod(undefined)).toBe('bonus')
  })

  it('sums by method, and the three rows add up exactly to the engine total', () => {
    const computed = [
      row('LUONG', [10, 10, 20, 20]),
      row('PHU_CAP', [1, 1, 2, 2]),
      row('BH', [3, 3, 5, 5]),
      row('T13', [0, 0, 0, 40]),
      row('QUA', [4, 0, 0, 0]),
      row('DL', [0, 50, 0, 0]),
    ]
    const out = buildCostBucketRows(computed, ITEMS, 4)
    expect(out.map((r) => [r.key, r.values, r.total])).toEqual([
      ['salary', [11, 11, 22, 22], 66],
      ['insurance', [3, 3, 5, 5], 16],
      ['bonus', [4, 50, 0, 40], 94],
    ])
    const engineTotal = computed.reduce((a, r) => a + r.total, 0)
    expect(out.reduce((a, r) => a + r.total, 0)).toBe(engineTotal)
  })

  it('puts an unknown code (no longer on the form) into the last row instead of dropping its money', () => {
    const out = buildCostBucketRows([row('LUONG', [1]), row('GONE', [7])], ITEMS, 1)
    expect(out.find((r) => r.key === 'bonus')?.total).toBe(7)
  })

  it('always keeps the salary row, drops empty other rows, and treats null cells as 0', () => {
    const out = buildCostBucketRows([{ code: 'LUONG', name: 'L', values: [null, 5], total: null }], ITEMS, 2)
    expect(out).toHaveLength(1)
    expect(out[0]).toMatchObject({ values: [0, 5], total: 0 })
    expect(buildCostBucketRows([], [], 4)).toEqual([
      { key: 'salary', label: 'Lương + phụ cấp', values: [0, 0, 0, 0], total: 0, items: [] },
    ])
  })
})

describe('headcount per sub-period', () => {
  it('adds every line and cleans junk (negative, fraction, blank) to non-negative ints', () => {
    expect(sumLineHeadcounts([{ headcounts: [0, 1, 1, 1] }, { headcounts: [4, 4, 5.9, -2] }], 4)).toEqual([4, 5, 6, 1])
  })

  it('pads short lines with 0 and returns zeros for no lines', () => {
    expect(sumLineHeadcounts([{ headcounts: [3] }], 3)).toEqual([3, 0, 0])
    expect(sumLineHeadcounts([], 2)).toEqual([0, 0])
  })
})
