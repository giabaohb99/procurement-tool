import { describe, expect, it } from 'vitest'

import { COST_CALC_METHOD_CODE, PLAN_PERIOD_TYPE_CODE } from '@/shared/constants/statuses'
import type { HrCostItem } from '../types/hr-cost'
import { buildSubPeriods } from '../utils/headcount-plan-periods'
import { buildCostItemColumns } from './hr-cost-item-columns'
import { buildHeadcountPlanLineColumns } from './headcount-plan-line-columns'

const M = COST_CALC_METHOD_CODE
const item = (code: string, calc_method: number, name = code): HrCostItem => ({
  code,
  name,
  group_id: 1,
  calc_method,
  rate: null,
  factor: null,
  cap_amount: null,
  amount: null,
  base_codes: [],
  applies_to: 1,
  position_ids: [],
  months: [],
  actual_source: 0,
  sort_order: 0,
})

const ITEMS = [
  item('LUONG', M.PER_HEAD_MONTH, 'Lương vị trí'),
  item('PC_CV', M.PER_HEAD_MONTH, 'PC chức vụ'),
  item('BHXH', M.PERCENT_OF),
  item('QUA', M.PER_HEAD_ONCE),
  item('DU_LICH', M.LUMP_SUM),
]

const keys = (periodType: number, opts: { showMoney?: boolean; readOnly?: boolean; items?: HrCostItem[] } = {}) =>
  buildHeadcountPlanLineColumns({
    periods: buildSubPeriods(periodType, 1),
    items: opts.items ?? ITEMS,
    showMoney: opts.showMoney ?? true,
    readOnly: opts.readOnly ?? false,
  }).map((c) => c.key)

describe('position table columns', () => {
  it.each([
    [PLAN_PERIOD_TYPE_CODE.YEAR, 4],
    [PLAN_PERIOD_TYPE_CODE.HALF, 2],
    [PLAN_PERIOD_TYPE_CODE.QUARTER, 3],
    [PLAN_PERIOD_TYPE_CODE.MONTH, 1],
  ])('period type %i grows %i headcount columns', (type, n) => {
    expect(keys(type).filter((k) => k.startsWith('hc_'))).toHaveLength(n)
  })

  it('grows one amount column per per-position item only, in item order', () => {
    expect(keys(PLAN_PERIOD_TYPE_CODE.YEAR).filter((k) => k.startsWith('amt_'))).toEqual(['amt_LUONG', 'amt_PC_CV'])
  })

  it('names amount columns after the item so the user knows what to type', () => {
    const cols = buildHeadcountPlanLineColumns({
      periods: buildSubPeriods(1, 1),
      items: ITEMS,
      showMoney: true,
      readOnly: false,
    })
    expect(cols.find((c) => c.key === 'amt_LUONG')?.header).toBe('Lương vị trí / người / tháng')
  })

  it('removes every amount column when money is masked, but keeps headcount, current and hires', () => {
    const k = keys(PLAN_PERIOD_TYPE_CODE.YEAR, { showMoney: false })
    expect(k.some((x) => x.startsWith('amt_'))).toBe(false)
    expect(k).toEqual(expect.arrayContaining(['position', 'hc_0', 'hc_3', 'current', 'need']))
  })

  it('has no amount column when the plan has no per-position item, and no actions when read-only', () => {
    const k = keys(PLAN_PERIOD_TYPE_CODE.YEAR, { items: [], readOnly: true })
    expect(k.some((x) => x.startsWith('amt_'))).toBe(false)
    expect(k).not.toContain('actions')
  })

  it('does not collide when an item code looks like a headcount key', () => {
    const k = keys(PLAN_PERIOD_TYPE_CODE.YEAR, { items: [item('hc_0', M.PER_HEAD_MONTH)] })
    expect(new Set(k).size).toBe(k.length)
  })
})

describe('cost item table columns', () => {
  it('drops cap and amount columns when money is masked', () => {
    const k = buildCostItemColumns(false, false).map((c) => c.key)
    expect(k).not.toContain('cap_amount')
    expect(k).not.toContain('amount')
    expect(k).toContain('rate')
  })

  it('drops the actions column when read-only', () => {
    expect(buildCostItemColumns(true, true).map((c) => c.key)).not.toContain('actions')
  })
})
