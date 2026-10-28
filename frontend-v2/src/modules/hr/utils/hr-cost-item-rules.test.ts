import { describe, expect, it } from 'vitest'

import {
  COST_ACTUAL_SOURCE_CODE,
  COST_APPLIES_TO_CODE,
  COST_CALC_METHOD,
  COST_CALC_METHOD_CODE,
} from '@/shared/constants/statuses'
import type { HeadcountPlanLine } from '../types/headcount-plan'
import type { HrCostItem } from '../types/hr-cost'
import {
  changeCostItemMethod,
  createEmptyCostItem,
  describeCostItemFields,
  isItemAppliedToPosition,
  listBaseCandidates,
  listActualSourcesFor,
  listCostItemProblems,
  listPerPositionItems,
  moveCostItem,
  normalizeCostCode,
  removeCostItem,
  renameCostItemCode,
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

describe('changing the calc method', () => {
  it('drops values that no longer mean anything instead of sending a ghost rate', () => {
    const pct = item('BHXH', M.PERCENT_OF, { rate: 17.5, cap_amount: 46_800_000, base_codes: ['LUONG'] })
    const lump = changeCostItemMethod(pct, M.LUMP_SUM)
    expect(lump).toMatchObject({ rate: null, cap_amount: null, base_codes: [] })
  })

  it('pulls "whole department" back to all positions when the new method cannot use it', () => {
    const lump = item('DL', M.LUMP_SUM, { applies_to: COST_APPLIES_TO_CODE.WHOLE_DEPARTMENT })
    expect(changeCostItemMethod(lump, M.PER_HEAD_ONCE).applies_to).toBe(COST_APPLIES_TO_CODE.ALL_POSITIONS)
  })

  it('keeps only one base when switching % → months-of, and defaults the factor to 1', () => {
    const pct = item('X', M.PERCENT_OF, { base_codes: ['A', 'B'] })
    expect(changeCostItemMethod(pct, M.MONTHS_OF)).toMatchObject({ base_codes: ['A'], factor: 1 })
  })
})

describe('base candidates (no reference loops, doc 06 §4.2)', () => {
  const items = [
    item('LUONG', M.PER_HEAD_MONTH),
    item('T13', M.MONTHS_OF, { base_codes: ['LUONG'], months: [12] }),
    item('BHXH', M.PERCENT_OF, { base_codes: ['LUONG'] }),
    item('QUA', M.PER_HEAD_ONCE),
  ]

  it('lets % point only at per-position or months-of items, never at itself or another %', () => {
    const codes = listBaseCandidates(items, items[2]).map((i) => i.code)
    expect(codes).toEqual(['LUONG', 'T13'])
  })

  it('lets months-of point only at per-position items', () => {
    expect(listBaseCandidates(items, items[1]).map((i) => i.code)).toEqual(['LUONG'])
  })

  it('offers nothing to methods that have no base', () => {
    expect(listBaseCandidates(items, items[0])).toEqual([])
  })

  it('ignores items whose code is still blank', () => {
    expect(listBaseCandidates([...items, item('', M.PER_HEAD_MONTH)], items[2]).map((i) => i.code)).not.toContain('')
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

describe('renaming a code keeps every reference in sync', () => {
  const items = [item('LUONG', M.PER_HEAD_MONTH), item('BHXH', M.PERCENT_OF, { base_codes: ['LUONG'] })]
  const lines = [line(5, { LUONG: 12_000_000 }), line(0, null)]

  it('moves base_codes and the per-position amounts to the new code', () => {
    const r = renameCostItemCode(items, lines, 'LUONG', 'luong vi tri')
    expect(r.items.map((i) => i.code)).toEqual(['LUONG_VI_TRI', 'BHXH'])
    expect(r.items[1].base_codes).toEqual(['LUONG_VI_TRI'])
    expect(r.lines[0].amounts).toEqual({ LUONG_VI_TRI: 12_000_000 })
    //  Dòng của người không thấy tiền (`amounts: null`) không được biến thành `{}`.
    expect(r.lines[1].amounts).toBeNull()
  })

  it('refuses a rename onto another item’s code — two items would merge silently', () => {
    const r = renameCostItemCode(items, lines, 'LUONG', 'bhxh')
    expect(r.items.map((i) => i.code)).toEqual(['LUONG', 'BHXH'])
  })

  it('refuses an empty code', () => {
    expect(renameCostItemCode(items, lines, 'LUONG', '  ').items[0].code).toBe('LUONG')
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
  it('renumbers sort_order 10·20·30 after a move and ignores moves past the ends', () => {
    const items = [item('A', 1), item('B', 1), item('C', 1)]
    expect(moveCostItem(items, 2, 1).map((i) => i.code)).toEqual(['A', 'B', 'C'])
    const moved = moveCostItem(items, 2, -1)
    expect(moved.map((i) => [i.code, i.sort_order])).toEqual([['A', 10], ['C', 20], ['B', 30]])
    expect(moveCostItem([], 0, 1)).toEqual([])
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

describe('early problems (what the backend would reject with 422)', () => {
  it('flags a duplicate code, a missing base, months outside the period and an empty position pick', () => {
    const items = [
      item('A', 1),
      item('A', 1),
      item('B', M.MONTHS_OF, { months: [12] }),
      item('C', 1, { applies_to: COST_APPLIES_TO_CODE.SELECTED_POSITIONS }),
    ]
    expect(listCostItemProblems(items[0], items)).toContain('Mã «A» bị trùng.')
    expect(listCostItemProblems(items[2], items, [7, 8, 9])).toEqual([
      'Chưa chọn khoản gốc.',
      'Có tháng rơi vào nằm ngoài kỳ của kế hoạch.',
    ])
    expect(listCostItemProblems(items[3], items)).toContain('Chọn «Các vị trí đã chọn» nhưng chưa chọn vị trí nào.')
  })

  it('does not check months against a period on the template screen (no period there)', () => {
    const b = item('B', M.PER_HEAD_ONCE, { months: [12] })
    expect(listCostItemProblems(b, [b])).toEqual([])
  })

  it('flags a base that points at a percent item (would loop)', () => {
    const items = [item('P', M.PERCENT_OF, { base_codes: ['A'] }), item('A', M.PERCENT_OF, { base_codes: ['P'] })]
    expect(listCostItemProblems(items[0], items)).toContain('Khoản gốc không hợp lệ (đã bỏ hoặc sai cách tính).')
  })
})

describe('actual source vs calc method (khớp backend costing._check_actual_source)', () => {
  const S = COST_ACTUAL_SOURCE_CODE

  it('offers only the sources the backend accepts', () => {
    expect(listActualSourcesFor(M.PER_HEAD_MONTH)).toEqual([S.NONE, S.BASE_SALARY, S.ALLOWANCE])
    expect(listActualSourcesFor(M.PERCENT_OF)).toEqual([S.NONE, S.PERCENT_OF_INSURANCE_SALARY])
    expect(listActualSourcesFor(M.PER_HEAD_ONCE)).toEqual([S.NONE])
    expect(listActualSourcesFor(M.LUMP_SUM)).toEqual([S.NONE])
  })

  it('drops an incompatible source when the method changes, keeps a compatible one', () => {
    expect(changeCostItemMethod(item('A', M.PER_HEAD_MONTH, { actual_source: S.BASE_SALARY }), M.PERCENT_OF).actual_source).toBe(S.NONE)
    expect(changeCostItemMethod(item('A', M.PERCENT_OF, { actual_source: S.PERCENT_OF_INSURANCE_SALARY }), M.PERCENT_OF).actual_source).toBe(
      S.PERCENT_OF_INSURANCE_SALARY,
    )
  })

  it('flags an incompatible source and a once-per-head item without months', () => {
    const bad = item('A', M.PER_HEAD_MONTH, { actual_source: S.PERCENT_OF_INSURANCE_SALARY })
    expect(listCostItemProblems(bad, [bad])).toContain('Nguồn thực tế không dùng được với cách tính này.')
    const once = item('B', M.PER_HEAD_ONCE)
    expect(listCostItemProblems(once, [once])).toContain('Chưa chọn tháng rơi vào.')
  })
})
