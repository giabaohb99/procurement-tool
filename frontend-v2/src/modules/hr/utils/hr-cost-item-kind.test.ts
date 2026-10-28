import { describe, expect, it } from 'vitest'

import {
  COST_ACTUAL_SOURCE_CODE,
  COST_APPLIES_TO_CODE,
  COST_CALC_METHOD,
  COST_CALC_METHOD_CODE,
} from '@/shared/constants/statuses'
import type { HrCostGroup, HrCostItem } from '../types/hr-cost'
import {
  applyCostAutoDefaults,
  findCostGroupId,
  getCostItemKind,
  pickAutoActualSource,
  pickDefaultMonthsBase,
  pickDefaultPercentBases,
} from './hr-cost-item-kind'

const M = COST_CALC_METHOD_CODE
const S = COST_ACTUAL_SOURCE_CODE

const item = (code: string, calc_method: number, over: Partial<HrCostItem> = {}): HrCostItem => ({
  code,
  name: code,
  group_id: 1,
  calc_method,
  rate: null,
  factor: null,
  cap_amount: null,
  amount: null,
  base_codes: [],
  applies_to: COST_APPLIES_TO_CODE.ALL_POSITIONS,
  position_ids: [],
  months: [],
  actual_source: 0,
  sort_order: 0,
  ...over,
})

const group = (id: number, name: string, is_active = true): HrCostGroup => ({ id, name, sort_order: id, is_active })
const GROUPS = [group(1, 'Quỹ lương'), group(2, 'Bắt buộc theo luật'), group(3, 'Phúc lợi'), group(4, 'Khác')]
const OTHERS = [
  item('PC', M.PER_HEAD_MONTH, { actual_source: S.ALLOWANCE }),
  item('LUONG', M.PER_HEAD_MONTH, { actual_source: S.BASE_SALARY }),
  item('BH', M.PERCENT_OF),
]

describe('three user-facing kinds over five backend methods', () => {
  it('maps every generated method to a kind — a new backend code must not vanish from the radio', () => {
    for (const o of COST_CALC_METHOD) expect(['monthly', 'percent', 'batch']).toContain(getCostItemKind(Number(o.value)))
    expect([M.MONTHS_OF, M.PER_HEAD_ONCE, M.LUMP_SUM].map(getCostItemKind)).toEqual(['batch', 'batch', 'batch'])
  })

  it('percent bases default to EVERY monthly item, never to another percent', () => {
    expect(pickDefaultPercentBases(OTHERS)).toEqual(['PC', 'LUONG'])
  })

  it('months-of takes the salary item as base, else the first monthly item, else nothing', () => {
    expect(pickDefaultMonthsBase(OTHERS)).toEqual(['LUONG'])
    expect(pickDefaultMonthsBase([item('A', M.PER_HEAD_MONTH), item('B', M.PER_HEAD_MONTH)])).toEqual(['A'])
    expect(pickDefaultMonthsBase([item('BH', M.PERCENT_OF)])).toEqual([])
  })

  it('ignores monthly items whose code is still blank', () => {
    expect(pickDefaultPercentBases([item('', M.PER_HEAD_MONTH)])).toEqual([])
  })
})

describe('group and actual-source auto defaults', () => {
  it('finds the group by name regardless of accents/case, preferring an active one', () => {
    expect(findCostGroupId(GROUPS, 'quy luong')).toBe(1)
    expect(findCostGroupId([group(9, 'Phúc lợi', false), group(10, 'phúc lợi')], 'Phúc lợi')).toBe(10)
  })

  it('falls back to the first group, and to 0 when the catalog is empty', () => {
    expect(findCostGroupId([group(7, 'Chi khác')], 'Phúc lợi')).toBe(7)
    expect(findCostGroupId([], 'Phúc lợi')).toBe(0)
  })

  it('reads salary / allowance from the name only for monthly items', () => {
    expect(pickAutoActualSource({ name: 'Lương vị trí', calc_method: M.PER_HEAD_MONTH })).toBe(S.BASE_SALARY)
    expect(pickAutoActualSource({ name: 'Phụ cấp lương', calc_method: M.PER_HEAD_MONTH })).toBe(S.ALLOWANCE)
    expect(pickAutoActualSource({ name: 'Ăn trưa', calc_method: M.PER_HEAD_MONTH })).toBe(S.NONE)
    //  «Thưởng» chứa «uong» nhưng không phải «lương» — không được dò nhầm.
    expect(pickAutoActualSource({ name: 'Thưởng', calc_method: M.PER_HEAD_MONTH })).toBe(S.NONE)
    expect(pickAutoActualSource({ name: 'BH', calc_method: M.PERCENT_OF })).toBe(S.PERCENT_OF_INSURANCE_SALARY)
    expect(pickAutoActualSource({ name: 'Lương tháng 13', calc_method: M.MONTHS_OF })).toBe(S.NONE)
  })

  it('sets group and actual source from the method alone — the dialog has no field for them', () => {
    const x = item('X', M.PERCENT_OF, { group_id: 4, actual_source: S.NONE })
    expect(applyCostAutoDefaults(x, GROUPS)).toMatchObject({ group_id: 2, actual_source: S.PERCENT_OF_INSURANCE_SALARY })
  })

  it('keeps the current group when the catalog is empty instead of zeroing it', () => {
    expect(applyCostAutoDefaults(item('X', M.PER_HEAD_ONCE, { group_id: 5 }), []).group_id).toBe(5)
  })
})
