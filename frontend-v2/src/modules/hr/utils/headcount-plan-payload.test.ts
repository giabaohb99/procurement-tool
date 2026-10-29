import { describe, expect, it } from 'vitest'

import { COST_CALC_METHOD_CODE } from '@/shared/constants/statuses'
import type { HrCostItem } from '../types/hr-cost'
import { applyTemplateToDraft, createEmptyDraft, type HeadcountPlanDraft } from './headcount-plan-draft'
import { buildCreatePayload, buildDraftPayload, buildPlanPayload } from './headcount-plan-payload'

const M = COST_CALC_METHOD_CODE

const item = (code: string, calc_method: number, over: Partial<HrCostItem> = {}): HrCostItem => ({
  id: 3,
  code,
  name: ` ${code} `,
  group_id: 1,
  calc_method,
  rate: null,
  factor: null,
  cap_amount: 46_800_000,
  amount: 500_000,
  base_codes: [],
  applies_to: 1,
  position_ids: [],
  months: [12, 3],
  actual_source: 0,
  sort_order: 10,
  ...over,
})

const draft = (over: Partial<HeadcountPlanDraft> = {}): HeadcountPlanDraft => ({
  ...createEmptyDraft(2026),
  company_id: 1,
  department_id: 11,
  basis_no: ' 12/QĐ-BGĐ ',
  cost_items: [item('LUONG', M.PER_HEAD_MONTH)],
  lines: [
    { id: 8, position_id: 5, position_name: 'KTV', headcounts: [4, 4, 5.9, -1], amounts: { LUONG: 12_000_000 }, note: '' },
  ],
  documents: [
    { document_id: 1, can_read: true, code: 'QĐ-1', title: 'Duyệt ngân sách' },
    { document_id: 2, can_read: false },
    { document_id: 3, can_read: false, deleted: true },
  ],
  ...over,
})

/** Mọi khóa của một object (cả lồng nhau) — để soi khóa thừa backend `extra="forbid"` sẽ 422. */
const keysOf = (o: object) => Object.keys(o).sort()

describe('compute draft payload (POST /compute — PlanDraft, extra="forbid")', () => {
  const p = buildDraftPayload(draft(), true)

  it('sends exactly the PlanDraft keys — no document_ids, no template_id', () => {
    expect(keysOf(p)).toEqual(
      ['approver_employee_id', 'basis_date', 'basis_no', 'company_id', 'cost_items', 'department_id', 'lines', 'note', 'period_no', 'period_type', 'year'].sort(),
    )
  })

  it('strips item id and line id / position_name, which the schema forbids', () => {
    expect(p.cost_items[0]).not.toHaveProperty('id')
    expect(keysOf(p.lines[0])).toEqual(['amounts', 'headcounts', 'note', 'position_id'])
  })

  it('sends rate / factor as numbers (schema float default 0), never null', () => {
    expect(p.cost_items[0]).toMatchObject({ rate: 0, factor: 0 })
  })

  it('cleans headcounts to non-negative ints and sorts months', () => {
    expect(p.lines[0].headcounts).toEqual([4, 4, 5, 0])
    expect(p.cost_items[0].months).toEqual([3, 12])
  })

  it('trims text fields and sends an empty basis date as null', () => {
    expect(p.basis_no).toBe('12/QĐ-BGĐ')
    expect(p.cost_items[0].name).toBe('LUONG')
    expect(p.basis_date).toBeNull()
  })

  it('drops null amounts inside a line — dict[str, int] rejects a single null', () => {
    const q = buildDraftPayload(
      draft({ lines: [{ position_id: 5, headcounts: [1], amounts: { LUONG: null as unknown as number, PC: 1 }, note: '' }] }),
      true,
    )
    expect(q.lines[0].amounts).toEqual({ PC: 1 })
  })
})

describe('money masking in payloads', () => {
  it('sends every money cell as null for a viewer who cannot see pay — null keeps the stored value, a number 403s', () => {
    const p = buildPlanPayload(draft(), false)
    expect(p.cost_items[0]).toMatchObject({ cap_amount: null, amount: null })
    expect(p.lines[0].amounts).toBeNull()
  })

  it('sends real numbers for a payroll viewer, with 0 instead of null for a cleared cell', () => {
    const p = buildPlanPayload(draft({ cost_items: [item('X', M.LUMP_SUM, { amount: null })] }), true)
    expect(p.cost_items[0]).toMatchObject({ amount: 0, cap_amount: 46_800_000 })
  })
})

describe('PUT payload keeps links the saver cannot see', () => {
  it('keeps unreadable documents (PUT replaces the list) and drops deleted ones', () => {
    expect(buildPlanPayload(draft(), true).document_ids).toEqual([1, 2])
  })
})

describe('create payload (POST /)', () => {
  const tpl = [item('LUONG', M.PER_HEAD_MONTH)]

  it('lets the backend copy the template when the user did not touch the items', () => {
    const d = { ...applyTemplateToDraft(draft(), 9, tpl), company_id: 1 }
    const p = buildCreatePayload(d, true)
    expect(p.template_id).toBe(9)
    expect(p).not.toHaveProperty('cost_items')
    expect(p.document_ids).toEqual([1, 2])
  })

  it('sends the edited items once the user changed them — otherwise the edits vanish silently', () => {
    const d = { ...applyTemplateToDraft(draft(), 9, tpl), cost_items_edited: true }
    expect(buildCreatePayload(d, true).cost_items).toHaveLength(1)
  })
})

describe('switched-off items (khối «Chi phí khác»)', () => {
  it('are left out of both the preview and the saved plan, with every reference to them', () => {
    const d = draft({
      cost_items: [
        item('LUONG', M.PER_HEAD_MONTH, { months: [] }),
        item('T13', M.MONTHS_OF, { factor: 1, base_codes: ['LUONG'], months: [12], excluded: true }),
        item('QUA', M.PER_HEAD_ONCE, { months: [3] }),
      ],
    })
    expect(buildDraftPayload(d, true).cost_items.map((i) => i.code)).toEqual(['LUONG', 'QUA'])
    expect(buildPlanPayload(d, true).cost_items.map((i) => i.code)).toEqual(['LUONG', 'QUA'])
  })

  it('never leaks the UI-only flag into the 14 backend keys', () => {
    const d = draft({ cost_items: [item('LUONG', M.PER_HEAD_MONTH, { excluded: false })] })
    expect(Object.keys(buildDraftPayload(d, true).cost_items[0])).toHaveLength(14)
    expect(buildDraftPayload(d, true).cost_items[0]).not.toHaveProperty('excluded')
  })

  it('a set built on screen (template_id 0) is always sent on create', () => {
    const d = { ...draft(), template_id: 0 }
    expect(buildCreatePayload(d, true).cost_items).toHaveLength(1)
  })
})
