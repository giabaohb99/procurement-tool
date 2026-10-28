import { describe, expect, it } from 'vitest'

import { COST_ACTUAL_SOURCE_CODE, COST_APPLIES_TO_CODE, COST_CALC_METHOD_CODE } from '@/shared/constants/statuses'
import type { HrCostItem } from '../types/hr-cost'
import { toCostItemPayload } from './headcount-plan-payload'
import {
  detectCostCustomParts,
  finalizeCostItems,
  markCostItemsCustomSetup,
} from './hr-cost-item-custom'

const M = COST_CALC_METHOD_CODE
const A = COST_APPLIES_TO_CODE
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
  applies_to: calc_method === M.LUMP_SUM ? A.WHOLE_DEPARTMENT : A.ALL_POSITIONS,
  position_ids: [],
  months: [],
  actual_source: 0,
  sort_order: 0,
  ...over,
})

const SALARY = item('LUONG', M.PER_HEAD_MONTH, { actual_source: S.BASE_SALARY })
const ALLOW = item('PC', M.PER_HEAD_MONTH)
const BH = item('BH', M.PERCENT_OF, { rate: 23.5, base_codes: ['LUONG', 'PC'] })
const BONUS = item('T13', M.MONTHS_OF, { factor: 1, base_codes: ['LUONG'], months: [12] })

describe('percent items always sit on EVERY monthly item', () => {
  it('a monthly item added after the insurance item is still counted when the list is finalized', () => {
    const lunch = item('AN_TRUA', M.PER_HEAD_MONTH)
    const out = finalizeCostItems([SALARY, BH, lunch])
    expect(out[1].base_codes).toEqual(['LUONG', 'AN_TRUA'])
  })

  it('deleting the last monthly item leaves the percent item with no base (the dialog then says so)', () => {
    expect(finalizeCostItems([BH])[0].base_codes).toEqual([])
  })

  it('months-of follows the item whose actual source is salary, else the first monthly item', () => {
    expect(finalizeCostItems([ALLOW, SALARY, BONUS])[2].base_codes).toEqual(['LUONG'])
    expect(finalizeCostItems([ALLOW, { ...SALARY, actual_source: S.NONE }, BONUS])[2].base_codes).toEqual(['PC'])
  })

  it('numbers the order by list position and forces «all positions» / «whole department»', () => {
    const out = finalizeCostItems([item('Q', M.PER_HEAD_ONCE, { sort_order: 999 }), item('L', M.LUMP_SUM, { applies_to: A.ALL_POSITIONS })])
    expect(out.map((i) => i.sort_order)).toEqual([10, 20])
    expect(out[1].applies_to).toBe(A.WHOLE_DEPARTMENT)
  })
})

describe('old items whose setup the short form cannot show', () => {
  it('a plain set needs nothing kept', () => {
    expect(markCostItemsCustomSetup([SALARY, ALLOW, BH, BONUS]).every((i) => i.custom_parts === undefined)).toBe(true)
  })

  it('detects selected positions, a partial base and months on a monthly / percent item', () => {
    const onlySalary = { ...BH, base_codes: ['LUONG'] }
    expect(detectCostCustomParts(onlySalary, [SALARY, ALLOW])).toEqual(['bases'])
    const somePositions = item('X', M.PER_HEAD_MONTH, { applies_to: A.SELECTED_POSITIONS, position_ids: [7], months: [1, 2] })
    expect(detectCostCustomParts(somePositions, [])).toEqual(['applies', 'months'])
    expect(detectCostCustomParts({ ...BH, months: [6] }, [SALARY, ALLOW])).toEqual(['months'])
  })

  it('a whole-department item spread over every month is plain («chia đều» is in the sentence)', () => {
    expect(detectCostCustomParts(item('L', M.LUMP_SUM, { amount: 1 }), [])).toEqual([])
    expect(detectCostCustomParts(item('L', M.LUMP_SUM, { amount: 1, months: [6] }), [])).toEqual([])
  })

  it('a batch item paid in several months cannot fit the single «chi tháng» box — kept as is', () => {
    expect(detectCostCustomParts(item('Q', M.PER_HEAD_ONCE, { amount: 1, months: [3, 10] }), [])).toEqual(['months'])
    expect(detectCostCustomParts({ ...BONUS, months: [6, 12] }, [SALARY])).toEqual(['months'])
    expect(detectCostCustomParts(item('L', M.LUMP_SUM, { amount: 1, months: [1, 7] }), [])).toEqual(['months'])
  })

  it('a percent base that includes a months-of item is not «all monthly items» — kept', () => {
    expect(detectCostCustomParts({ ...BH, base_codes: ['LUONG', 'PC', 'T13'] }, [SALARY, ALLOW, BONUS])).toEqual(['bases'])
  })

  it('saving keeps the custom parts untouched even after another monthly item is added', () => {
    const [s, a, bh] = markCostItemsCustomSetup([SALARY, ALLOW, { ...BH, base_codes: ['LUONG'], applies_to: A.SELECTED_POSITIONS, position_ids: [3] }])
    const lunch = item('AN_TRUA', M.PER_HEAD_MONTH)
    const out = finalizeCostItems([s, a, bh, lunch])
    expect(out[2]).toMatchObject({ base_codes: ['LUONG'], applies_to: A.SELECTED_POSITIONS, position_ids: [3] })
    //  Cờ chỉ sống ở giao diện — payload vẫn đúng 14 khóa.
    expect(Object.keys(toCostItemPayload(out[2], true))).toHaveLength(14)
    expect(toCostItemPayload(out[2], true)).not.toHaveProperty('custom_parts')
  })
})
