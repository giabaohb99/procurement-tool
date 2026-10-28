import { describe, expect, it } from 'vitest'

import { COST_ACTUAL_SOURCE_CODE, COST_CALC_METHOD_CODE } from '@/shared/constants/statuses'
import type { HrCostGroup, HrCostItem } from '../types/hr-cost'
import { toCostItemPayload } from './headcount-plan-payload'
import {
  INSURANCE_CAP_HINT_AMOUNT,
  OTHER_COST_KINDS,
  buildOtherCostItem,
  buildSuggestedCostItems,
  describePerHeadColumn,
  ensureSalaryItems,
  pickSuggestedTemplateId,
} from './hr-cost-item-presets'
import { listOtherCostProblems } from './hr-cost-item-validation'

const M = COST_CALC_METHOD_CODE
const S = COST_ACTUAL_SOURCE_CODE
const group = (id: number, name: string): HrCostGroup => ({ id, name, sort_order: id, is_active: true })
const GROUPS = [group(11, 'Quỹ lương'), group(12, 'Bắt buộc theo luật'), group(13, 'Phúc lợi'), group(14, 'Khác')]

/** Đúng 14 khóa của `CostItemIn` backend (`extra="forbid"`) — thừa / thiếu một khóa là 422. */
const BACKEND_KEYS = [
  'actual_source',
  'amount',
  'applies_to',
  'base_codes',
  'calc_method',
  'cap_amount',
  'code',
  'factor',
  'group_id',
  'months',
  'name',
  'position_ids',
  'rate',
  'sort_order',
]

describe('suggested set when the server has no active template', () => {
  it('is Lương · Phụ cấp · Bảo hiểm 23,5% on both · Thưởng 13 on Lương in T12 — same as «Mẫu gợi ý»', () => {
    const [salary, allowance, insurance, bonus] = buildSuggestedCostItems(GROUPS)
    expect(salary).toMatchObject({ code: 'LUONG', calc_method: M.PER_HEAD_MONTH, group_id: 11, actual_source: S.BASE_SALARY })
    expect(allowance).toMatchObject({ code: 'PHU_CAP', group_id: 11, actual_source: S.ALLOWANCE })
    expect(insurance).toMatchObject({
      calc_method: M.PERCENT_OF,
      rate: 23.5,
      cap_amount: INSURANCE_CAP_HINT_AMOUNT,
      base_codes: ['LUONG', 'PHU_CAP'],
      group_id: 12,
      actual_source: S.PERCENT_OF_INSURANCE_SALARY,
    })
    expect(bonus).toMatchObject({ calc_method: M.MONTHS_OF, factor: 1, base_codes: ['LUONG'], months: [12] })
  })

  it('moves the 13th-month bonus into a period that has no December', () => {
    expect(buildSuggestedCostItems(GROUPS, [7, 8, 9])[3].months).toEqual([9])
  })

  it('works with an empty group catalog (fresh install) — group 0, codes still fixed', () => {
    const items = buildSuggestedCostItems([])
    expect(items.map((i) => i.group_id)).toEqual([0, 0, 0, 0])
    expect(items.slice(0, 2).map((i) => i.code)).toEqual(['LUONG', 'PHU_CAP'])
  })
})

describe('Lương and Phụ cấp are always there', () => {
  it('adds the missing ones at the top and says it did', () => {
    const bonus = buildOtherCostItem('per_head_once', { items: [], groups: GROUPS })
    const out = ensureSalaryItems([bonus], GROUPS)
    expect(out.added).toBe(true)
    expect(out.items.map((i) => i.code)).toEqual(['LUONG', 'PHU_CAP', bonus.code])
  })

  it('leaves a complete set alone (same items, added = false)', () => {
    const full = buildSuggestedCostItems(GROUPS)
    const out = ensureSalaryItems(full, GROUPS)
    expect(out.added).toBe(false)
    expect(out.items).toEqual(full)
  })

  it('an old set whose salary has another code still gets LUONG — the column is fixed by code', () => {
    const old = { ...buildSuggestedCostItems(GROUPS)[0], code: 'QUY_LUONG', name: 'Quỹ lương (nhập tổng)' }
    expect(ensureSalaryItems([old], GROUPS).items.map((i) => i.code)).toEqual(['LUONG', 'PHU_CAP', 'QUY_LUONG'])
  })
})

describe('«Thêm chi phí» — four kinds', () => {
  const base = buildSuggestedCostItems(GROUPS).slice(0, 2)

  it('offers exactly the four kinds in the agreed order and labels', () => {
    expect(OTHER_COST_KINDS.map((k) => k.label)).toEqual(['% trên lương', 'Số tháng lương', 'Theo đợt mỗi người', 'Cả phòng'])
  })

  it('maps each kind onto backend methods 2…5 with a suggested name', () => {
    const out = OTHER_COST_KINDS.map((k) => buildOtherCostItem(k.kind, { items: base, groups: GROUPS }))
    expect(out.map((i) => i.calc_method)).toEqual([M.PERCENT_OF, M.MONTHS_OF, M.PER_HEAD_ONCE, M.LUMP_SUM])
    expect(out.every((i) => i.name.trim().length > 0)).toBe(true)
    //  Cả phòng: không tháng = chia đều; áp «cả phòng» ngay từ đầu (backend 422 nếu khoản khác mang cờ này).
    expect(out[3]).toMatchObject({ months: [], applies_to: 3 })
  })

  it('a second % item is not another 23,5% insurance copy', () => {
    const first = buildOtherCostItem('percent', { items: base, groups: GROUPS })
    const second = buildOtherCostItem('percent', { items: [...base, first], groups: GROUPS })
    expect(first.rate).toBe(23.5)
    expect(second).toMatchObject({ rate: null, cap_amount: null })
    expect(second.code).not.toBe(first.code)
  })

  it('once-per-head starts in the first month of the period, never outside it', () => {
    const q3 = buildOtherCostItem('per_head_once', { items: base, groups: GROUPS, periodMonths: [7, 8, 9] })
    expect(q3.months).toEqual([7])
    expect(listOtherCostProblems(q3, base, { periodMonths: [7, 8, 9] })).toEqual(['Nhập số tiền lớn hơn 0.'])
  })

  it('never repeats a code when the same kind is added twice', () => {
    const a = buildOtherCostItem('lump_sum', { items: base, groups: GROUPS })
    const b = buildOtherCostItem('lump_sum', { items: [...base, a], groups: GROUPS })
    expect(new Set([a.code, b.code]).size).toBe(2)
  })

  it('sends exactly the backend keys — the simplified UI must not change the payload shape', () => {
    const all = [...buildSuggestedCostItems(GROUPS), ...OTHER_COST_KINDS.map((k) => buildOtherCostItem(k.kind, { items: base, groups: GROUPS }))]
    for (const it of all as HrCostItem[]) {
      expect(Object.keys(it).sort()).toEqual(BACKEND_KEYS)
      expect(Object.keys(toCostItemPayload(it, true)).sort()).toEqual(BACKEND_KEYS)
    }
  })
})

describe('which template fills a new plan', () => {
  const t = (id: number, name: string, is_active = true) => ({ id, name, is_active })

  it('prefers the active «Mẫu gợi ý» whatever its position, accents or case', () => {
    expect(pickSuggestedTemplateId([t(1, 'Mẫu nhà máy'), t(2, 'mau goi y ')])).toBe(2)
  })

  it('skips an inactive «Mẫu gợi ý» and falls back to the first active template', () => {
    expect(pickSuggestedTemplateId([t(1, 'Mẫu gợi ý', false), t(5, 'Mẫu văn phòng')])).toBe(5)
  })

  it('returns 0 when there is no active template — the screen builds the suggested set itself', () => {
    expect(pickSuggestedTemplateId([])).toBe(0)
    expect(pickSuggestedTemplateId([t(1, 'Mẫu gợi ý', false)])).toBe(0)
  })
})

describe('money column titles of «Người và lương»', () => {
  it('reads Lương / Phụ cấp by code, other monthly items by name, a blank name by code', () => {
    expect(describePerHeadColumn({ code: 'LUONG', name: 'Lương vị trí' })).toBe('Lương/người')
    expect(describePerHeadColumn({ code: 'PHU_CAP', name: 'x' })).toBe('Phụ cấp/người')
    expect(describePerHeadColumn({ code: 'AN_TRUA', name: ' Ăn trưa ' })).toBe('Ăn trưa/người')
    expect(describePerHeadColumn({ code: 'QUY_LUONG', name: '' })).toBe('QUY_LUONG/người')
  })
})
