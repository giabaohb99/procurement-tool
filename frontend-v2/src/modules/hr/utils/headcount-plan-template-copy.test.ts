import { describe, expect, it } from 'vitest'

import { COST_CALC_METHOD_CODE } from '@/shared/constants/statuses'
import type { HrCostItem } from '../types/hr-cost'
import { copyTemplateItemsForPeriod } from './headcount-plan-template-copy'

const M = COST_CALC_METHOD_CODE

const item = (code: string, calc_method: number, over: Partial<HrCostItem> = {}): HrCostItem => ({
  code,
  name: `Khoản ${code}`,
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
  ...over,
})

const Q1 = [1, 2, 3]
const ALL = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

describe('copying template items into a period (mirror of backend copy_template_items)', () => {
  it('keeps everything for a full year', () => {
    const src = [item('LUONG', 1), item('T13', M.MONTHS_OF, { base_codes: ['LUONG'], months: [12] })]
    const r = copyTemplateItemsForPeriod(src, ALL)
    expect(r.items.map((i) => i.code)).toEqual(['LUONG', 'T13'])
    expect(r.skipped).toEqual([])
  })

  it('drops an item whose every month falls outside the period', () => {
    const r = copyTemplateItemsForPeriod([item('T13', M.MONTHS_OF, { base_codes: [], months: [12] })], Q1)
    expect(r.items).toEqual([])
    expect(r.skipped).toEqual(['Khoản T13'])
  })

  it('keeps an item with some months inside and trims the others', () => {
    const r = copyTemplateItemsForPeriod([item('QUA', M.PER_HEAD_ONCE, { months: [3, 12] })], Q1)
    expect(r.items[0].months).toEqual([3])
  })

  it('keeps an "every month" item (no months) in any period', () => {
    expect(copyTemplateItemsForPeriod([item('LUONG', 1)], [7]).items).toHaveLength(1)
  })

  it('cascades: a % whose only base was dropped is dropped, a % with another base just loses one', () => {
    const src = [
      item('LUONG', 1),
      item('T13', M.MONTHS_OF, { base_codes: ['LUONG'], months: [12] }),
      item('BH_T13', M.PERCENT_OF, { base_codes: ['T13'] }),
      item('BH_ALL', M.PERCENT_OF, { base_codes: ['LUONG', 'T13'] }),
    ]
    const r = copyTemplateItemsForPeriod(src, Q1)
    expect(r.items.map((i) => i.code)).toEqual(['LUONG', 'BH_ALL'])
    expect(r.items[1].base_codes).toEqual(['LUONG'])
    expect(r.skipped).toEqual(['Khoản T13', 'Khoản BH_T13'])
  })

  it('never mutates the template it copies from', () => {
    const src = [item('QUA', M.PER_HEAD_ONCE, { months: [3, 12], id: 5 })]
    const r = copyTemplateItemsForPeriod(src, Q1)
    expect(src[0].months).toEqual([3, 12])
    expect(r.items[0].id).toBeUndefined()
  })

  it('returns nothing for an empty template', () => {
    expect(copyTemplateItemsForPeriod([], ALL)).toEqual({ items: [], skipped: [] })
  })
})
