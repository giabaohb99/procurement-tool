import { describe, expect, it } from 'vitest'

import { COST_CALC_METHOD_CODE, PLAN_PERIOD_TYPE_CODE } from '@/shared/constants/statuses'
import type { HeadcountPlanLine, HeadcountPlanPositionStat } from '../types/headcount-plan'
import type { HrCostItem } from '../types/hr-cost'
import {
  addDraftLine,
  applySeedToDraft,
  applyTemplateToDraft,
  changeDraftPeriod,
  computeNeedToHire,
  countCurrentForLine,
  createEmptyDraft,
  fillLineHeadcounts,
  normalizeCostItem,
} from './headcount-plan-draft'

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
  applies_to: 1,
  position_ids: [],
  months: [],
  actual_source: 0,
  sort_order: 0,
  ...over,
})

/** «Mẫu gợi ý» gieo sẵn ở backend (rút gọn): lương, BHXH % trên lương, thưởng tháng 13 rơi T12. */
const TEMPLATE = [
  item('LUONG', M.PER_HEAD_MONTH),
  item('BHXH', M.PERCENT_OF, { rate: 17.5, base_codes: ['LUONG'], cap_amount: 46_800_000 }),
  item('THUONG_13', M.MONTHS_OF, { factor: 1, base_codes: ['LUONG'], months: [12] }),
]

describe('changing the period of a draft', () => {
  it('resizes every line to the new number of sub-periods (backend 422s on a wrong length)', () => {
    let d = addDraftLine(createEmptyDraft(2026), 5, 'Kế toán viên')
    expect(d.lines[0].headcounts).toHaveLength(4)
    d = changeDraftPeriod(d, { period_type: PLAN_PERIOD_TYPE_CODE.QUARTER })
    expect(d.lines[0].headcounts).toHaveLength(3)
    d = changeDraftPeriod(d, { period_type: PLAN_PERIOD_TYPE_CODE.MONTH, period_no: 7 })
    expect(d.lines[0].headcounts).toHaveLength(1)
  })

  it('clamps the period number when the type shrinks (month 7 → quarter 4)', () => {
    const d = changeDraftPeriod({ ...createEmptyDraft(2026), period_type: PLAN_PERIOD_TYPE_CODE.MONTH, period_no: 7 }, {
      period_type: PLAN_PERIOD_TYPE_CODE.QUARTER,
    })
    expect(d.period_no).toBe(4)
  })

  it('re-copies an untouched template for the new period — Q1 has no 13th-month bonus', () => {
    let d = applyTemplateToDraft(createEmptyDraft(2026), 9, TEMPLATE)
    expect(d.cost_items.map((i) => i.code)).toEqual(['LUONG', 'BHXH', 'THUONG_13'])
    d = changeDraftPeriod(d, { period_type: PLAN_PERIOD_TYPE_CODE.QUARTER, period_no: 1 })
    expect(d.cost_items.map((i) => i.code)).toEqual(['LUONG', 'BHXH'])
    expect(d.skipped_items).toEqual(['THUONG_13'])
    d = changeDraftPeriod(d, { period_no: 4 })
    expect(d.cost_items.map((i) => i.code)).toEqual(['LUONG', 'BHXH', 'THUONG_13'])
    expect(d.skipped_items).toEqual([])
  })

  it('never overwrites cost items the user already edited', () => {
    const d = { ...applyTemplateToDraft(createEmptyDraft(2026), 9, TEMPLATE), cost_items_edited: true }
    const after = changeDraftPeriod(d, { period_type: PLAN_PERIOD_TYPE_CODE.QUARTER, period_no: 1 })
    expect(after.cost_items).toBe(d.cost_items)
  })
})

describe('applying a template', () => {
  it('drops the template item ids so the plan never posts another table’s primary key', () => {
    const d = applyTemplateToDraft(createEmptyDraft(2026), 9, [{ ...TEMPLATE[0], id: 77 }])
    expect(d.cost_items[0].id).toBeUndefined()
    expect(d.template_items?.[0].id).toBe(77)
  })

  it('turns Numeric strings from the API into numbers', () => {
    const raw = { ...TEMPLATE[1], rate: '17.5000' as unknown as number, factor: '' as unknown as number }
    expect(normalizeCostItem(raw)).toMatchObject({ rate: 17.5, factor: null })
  })
})

describe('adding a line', () => {
  it('refuses a second line for the same position (backend UNIQUE plan × position)', () => {
    const d = addDraftLine(addDraftLine(createEmptyDraft(2026), 5, 'A'), 5, 'A again')
    expect(d.lines).toHaveLength(1)
  })

  it('starts with zero headcount in every sub-period', () => {
    expect(addDraftLine(createEmptyDraft(2026), 0, 'Không theo vị trí').lines[0].headcounts).toEqual([0, 0, 0, 0])
  })
})

describe('current headcount and hires needed', () => {
  const stats: HeadcountPlanPositionStat[] = [
    { position_id: 5, position_name: 'KTV', current_count: 4, avg_base_salary: null, avg_allowance: null },
    { position_id: 6, position_name: 'KTT', current_count: 1, avg_base_salary: null, avg_allowance: null },
    { position_id: 0, position_name: 'Không theo vị trí', current_count: 2, avg_base_salary: null, avg_allowance: null },
  ]
  const ln = (position_id: number, headcounts: number[]): HeadcountPlanLine => ({
    position_id,
    headcounts,
    amounts: {},
    note: '',
  })

  it('counts a position line from its own stat, 0 when nobody holds it yet', () => {
    expect(countCurrentForLine(ln(5, [4]), [], stats)).toBe(4)
    expect(countCurrentForLine(ln(9, [1]), [], stats)).toBe(0)
  })

  it('counts the "no position" line as everyone NOT already on a position line — no double count', () => {
    const lines = [ln(5, [5]), ln(0, [3])]
    expect(countCurrentForLine(lines[1], lines, stats)).toBe(1 + 2)
    expect(countCurrentForLine(ln(0, [3]), [ln(0, [3])], stats)).toBe(7)
  })

  it('works with an empty stats list (company not chosen yet)', () => {
    expect(countCurrentForLine(ln(0, [3]), [], [])).toBe(0)
  })

  it('needs = last sub-period headcount − current; negative means over headcount', () => {
    expect(computeNeedToHire(ln(5, [0, 1, 1, 5]), 4)).toBe(1)
    expect(computeNeedToHire(ln(5, [3]), 4)).toBe(-1)
    expect(computeNeedToHire(ln(5, []), 2)).toBe(-2)
  })
})

describe('filling a new plan without a template picker', () => {
  const PHU_CAP = item('PHU_CAP', M.PER_HEAD_MONTH)

  it('copies a complete template as is and lets the backend copy it on create (template_id kept)', () => {
    const d = applySeedToDraft(createEmptyDraft(2026), { key: 't9', templateId: 9, items: [TEMPLATE[0], PHU_CAP] }, [])
    expect(d.template_id).toBe(9)
    expect(d.cost_items.map((i) => i.code)).toEqual(['LUONG', 'PHU_CAP'])
  })

  it('adds Lương / Phụ cấp when the template lacks them and then sends the whole set (template_id 0)', () => {
    const d = applySeedToDraft(createEmptyDraft(2026), { key: 't9', templateId: 9, items: TEMPLATE }, [])
    expect(d.cost_items.map((i) => i.code)).toEqual(['LUONG', 'PHU_CAP', 'BHXH', 'THUONG_13'])
    expect(d.template_id).toBe(0)
    //  Vẫn giữ bộ gốc để đổi kỳ thì chép lại (Q1 không có thưởng T12).
    expect(changeDraftPeriod(d, { period_type: PLAN_PERIOD_TYPE_CODE.QUARTER, period_no: 1 }).skipped_items).toEqual(['THUONG_13'])
  })

  it('a set built on screen (no template on the server) is sent as is', () => {
    const d = applySeedToDraft(createEmptyDraft(2026), { key: 'ui', templateId: 0, items: [TEMPLATE[0], PHU_CAP] }, [])
    expect(d.template_id).toBe(0)
    expect(d.cost_items).toHaveLength(2)
  })

  it('an empty template still ends up with the two salary columns', () => {
    const d = applySeedToDraft(createEmptyDraft(2026), { key: 't1', templateId: 1, items: [] }, [])
    expect(d.cost_items.map((i) => i.code)).toEqual(['LUONG', 'PHU_CAP'])
  })
})

describe('«Giống nhau cả năm»', () => {
  const line: HeadcountPlanLine = { position_id: 5, headcounts: [0, 1, 4, 4], amounts: null, note: 'x' }

  it('puts the same headcount into every sub-period and keeps the rest of the line', () => {
    expect(fillLineHeadcounts(line, 5)).toEqual({ ...line, headcounts: [5, 5, 5, 5] })
  })

  it('cleans a negative or fractional number to a non-negative int (backend rejects both)', () => {
    expect(fillLineHeadcounts(line, -3).headcounts).toEqual([0, 0, 0, 0])
    expect(fillLineHeadcounts(line, 2.7).headcounts).toEqual([2, 2, 2, 2])
    expect(fillLineHeadcounts({ ...line, headcounts: [] }, 3).headcounts).toEqual([])
  })
})
