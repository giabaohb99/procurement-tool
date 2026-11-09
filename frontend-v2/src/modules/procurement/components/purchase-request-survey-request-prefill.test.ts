import { describe, expect, it } from 'vitest'

import type {
  PurchaseRequestDetail,
  PurchaseRequestItem,
} from '../types/purchase-request-detail'
import { parseAssistantDraft } from '../utils/assistant-draft'
import { buildSurveyRequestPrefill } from './purchase-request-survey-request-prefill'

const LINE: PurchaseRequestItem = {
  id: 7,
  product_code: 'NAP0029',
  product_name: 'Nắp nhựa phi 28',
  item_group: 'Bao bì',
  group_desc: 'Hàng NCC có sẵn: 7 ngày',
  qty: 1000,
  unit: 'Cái',
  price: 900,
  vat_pct: 8,
  amount: 0,
  warehouse: '',
  required_date: '',
  assignee: '',
  expected_date: '',
  line_status: 'no_po',
  progress_note: '',
  note: 'Màu trắng',
  qty_ordered: 0,
  qty_received: 0,
  product_id: 3,
  product_thumbnail_url: '',
}

function request(items: PurchaseRequestItem[], overrides: Partial<PurchaseRequestDetail> = {}) {
  return {
    id: 12,
    code: 'PYC09112601',
    company_id: 2,
    company_name: 'DEGO',
    requester: 'Trần Bảo',
    requester_id: 9,
    requester_position: 'Nhân viên',
    department: 'Kế toán',
    head_of_dept: 'Lê Hà',
    purpose: 'Mua nắp chai',
    note: '',
    items,
    ...overrides,
  } as PurchaseRequestDetail
}

describe('buildSurveyRequestPrefill (CR-026 dời từ v1, duoc-CR-741)', () => {
  it('folds the product name and group description into the spec text, as v1 does', () => {
    const { fromPr } = buildSurveyRequestPrefill(request([LINE]))

    expect(fromPr.lines).toEqual([
      {
        received_date: '',
        result_due_date: '',
        item_group: 'Bao bì',
        requirement_detail: 'Nắp nhựa phi 28 — Hàng NCC có sẵn: 7 ngày',
        other_requirement: 'Màu trắng',
        request_qty: 1000,
        uom: 'Cái',
        proposed_price: 900,
        src_pr_item_id: 7,
      },
    ])
    expect(fromPr).toMatchObject({ pr_id: 12, pr_code: 'PYC09112601', requester_id: 9 })
  })

  it('skips nameless lines — an empty request yields no lines, and the page refuses to go on', () => {
    const { fromPr, assistantDraft } = buildSurveyRequestPrefill(
      request([{ ...LINE, product_name: '   ' }]),
    )
    expect(fromPr.lines).toEqual([])
    expect(assistantDraft.lines).toEqual([])
  })

  it('carries the department and head ids of the purchase request (review duoc-CR-741)', () => {
    const { fromPr } = buildSurveyRequestPrefill(
      request([LINE], { department_id: 31, head_of_dept_id: 44 }),
    )
    expect(fromPr).toMatchObject({
      department: 'Kế toán',
      department_id: 31,
      head_of_dept: 'Lê Hà',
      head_of_dept_id: 44,
    })
  })

  it('a request with no department id yields 0, never undefined', () => {
    const { fromPr } = buildSurveyRequestPrefill(request([LINE]))
    expect(fromPr.department_id).toBe(0)
    expect(fromPr.head_of_dept_id).toBe(0)
  })

  it('a line not yet saved carries src_pr_item_id 0, so no image is pulled across', () => {
    const { fromPr } = buildSurveyRequestPrefill(request([{ ...LINE, id: undefined }]))
    expect(fromPr.lines[0].src_pr_item_id).toBe(0)
  })

  it('the assistant-draft copy is accepted by the quote request screen as it is today', () => {
    const { assistantDraft } = buildSurveyRequestPrefill(request([LINE], { note: 'Gấp' }))

    //  Màn tạo YCBG v2 đọc gói này qua `parseAssistantDraft`; gói bị loại là điền hụt im lặng.
    const parsed = parseAssistantDraft(assistantDraft)
    expect(parsed?.lines).toHaveLength(1)
    expect(parsed?.note).toBe('Gấp\n(Tạo từ YCMH PYC09112601)')
    expect(parsed?.company_id).toBe(2)
  })
})
