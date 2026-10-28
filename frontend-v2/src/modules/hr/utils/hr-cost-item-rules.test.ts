import { describe, expect, it } from 'vitest'

import {
  COST_APPLIES_TO_CODE,
  COST_CALC_METHOD,
  COST_CALC_METHOD_CODE,
} from '@/shared/constants/statuses'
import type { HeadcountPlanLine } from '../types/headcount-plan'
import type { HrCostItem } from '../types/hr-cost'
import {
  createEmptyCostItem,
  dropExcludedCostItems,
  describeCostItemFields,
  isItemAppliedToPosition,
  listPerPositionItems,
  normalizeCostCode,
  removeCostItem,
  sortCostItemsByOrder,
} from './hr-cost-item-rules'

const M = COST_CALC_METHOD_CODE

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

const line = (position_id: number, amounts: Record<string, number> | null): HeadcountPlanLine => ({
  position_id,
  headcounts: [1, 1, 1, 1],
  amounts,
  note: '',
})

describe('field spec per calc method', () => {
  it('describes every generated calc method — a new backend code must not render a blank row', () => {
    for (const o of COST_CALC_METHOD) {
      const spec = describeCostItemFields(Number(o.value))
      expect(Object.values(spec).some(Boolean)).toBe(true)
    }
  })

  it('only lets the lump sum apply to the whole department', () => {
    expect(describeCostItemFields(M.LUMP_SUM).wholeDepartment).toBe(true)
    expect(describeCostItemFields(M.PER_HEAD_ONCE).wholeDepartment).toBe(false)
  })
})

describe('code normalisation', () => {
  it('produces the backend pattern ^[A-Za-z0-9_]+$ from Vietnamese input, capped at 30', () => {
    expect(normalizeCostCode('  Phụ cấp đóng BH ')).toBe('PHU_CAP_DONG_BH')
    expect(normalizeCostCode('Đ-ăn trưa!!')).toBe('D_AN_TRUA')
    expect(normalizeCostCode('x'.repeat(50))).toHaveLength(30)
    expect(normalizeCostCode('!!!')).toBe('')
  })
})

describe('removing an item', () => {
  it('strips it from other items’ bases and from line amounts', () => {
    const items = [item('LUONG', M.PER_HEAD_MONTH), item('PC', M.PER_HEAD_MONTH), item('BHXH', M.PERCENT_OF, { base_codes: ['LUONG', 'PC'] })]
    const r = removeCostItem(items, [line(5, { LUONG: 1, PC: 2 }), line(6, null)], 'PC')
    expect(r.items.map((i) => i.code)).toEqual(['LUONG', 'BHXH'])
    expect(r.items[1].base_codes).toEqual(['LUONG'])
    expect(r.lines[0].amounts).toEqual({ LUONG: 1 })
    expect(r.lines[1].amounts).toBeNull()
  })
})

describe('ordering and new items', () => {
  it('sorts by sort_order and keeps the current order on ties, without touching the input', () => {
    const items = [item('A', 1, { sort_order: 20 }), item('B', 1, { sort_order: 10 }), item('C', 1, { sort_order: 20 })]
    expect(sortCostItemsByOrder(items).map((i) => i.code)).toEqual(['B', 'A', 'C'])
    expect(items.map((i) => i.code)).toEqual(['A', 'B', 'C'])
    expect(sortCostItemsByOrder([])).toEqual([])
  })

  it('never hands out a code that already exists', () => {
    const fresh = createEmptyCostItem([item('KHOAN_2', 1), item('X', 1, { sort_order: 40 })])
    expect(fresh.code).toBe('KHOAN_3')
    expect(fresh.sort_order).toBe(50)
  })
})

describe('per-position columns and applicability', () => {
  it('only per-head-month items grow an amount column', () => {
    expect(listPerPositionItems([item('A', 1), item('B', 2), item('C', 5)]).map((i) => i.code)).toEqual(['A'])
  })

  it('locks the amount cell for positions outside "selected positions"', () => {
    const it2 = item('PCCV', 1, { applies_to: COST_APPLIES_TO_CODE.SELECTED_POSITIONS, position_ids: [3] })
    expect(isItemAppliedToPosition(it2, 3)).toBe(true)
    expect(isItemAppliedToPosition(it2, 4)).toBe(false)
    expect(isItemAppliedToPosition(it2, 0)).toBe(false)
  })
})

describe('switched-off items (khối «Chi phí khác»)', () => {
  it('drops every excluded item and strips it from other bases, leaving the rest untouched', () => {
    const items = [
      item('LUONG', M.PER_HEAD_MONTH),
      item('T13', M.MONTHS_OF, { base_codes: ['LUONG'], excluded: true }),
      item('BH', M.PERCENT_OF, { base_codes: ['LUONG', 'T13'] }),
    ]
    const out = dropExcludedCostItems(items, [line(1, { LUONG: 5 })])
    expect(out.items.map((i) => i.code)).toEqual(['LUONG', 'BH'])
    expect(out.items[1].base_codes).toEqual(['LUONG'])
    expect(out.lines[0].amounts).toEqual({ LUONG: 5 })
  })

  it('returns the same set when nothing is switched off, and an empty set stays empty', () => {
    expect(dropExcludedCostItems([item('A', M.PER_HEAD_ONCE)], []).items).toHaveLength(1)
    expect(dropExcludedCostItems([], [])).toEqual({ items: [], lines: [] })
  })
})
