import { describe, expect, it } from 'vitest'

import type { SurveyRequestFromPurchaseRequest } from './purchase-request-survey-request-prefill'
import type { SurveyRequestDetail } from '../types/survey-request-detail'
import {
  applySurveyRequestFromPurchaseRequest,
  keepsSourceDepartment,
  parseSurveyRequestFromPurchaseRequest,
} from './survey-request-from-purchase-request'

/** Gói đúng khuôn `buildSurveyRequestPrefill` của nút *Tạo yêu cầu báo giá* trên YCMH. */
const FROM_PR: SurveyRequestFromPurchaseRequest = {
  pr_id: 41,
  pr_code: 'PYC26110901',
  company_id: 3,
  requester: 'Nguyễn Văn A',
  requester_id: 77,
  requester_position: 'Chuyên viên',
  department: 'Marketing',
  head_of_dept: 'Trần Thị B',
  purpose: 'Mua thùng cho đợt hàng Tết',
  note: 'Cần gấp',
  lines: [
    {
      received_date: '',
      result_due_date: '2026-11-20',
      item_group: 'Bao bì',
      requirement_detail: 'Thùng carton — 5 lớp',
      other_requirement: 'In logo',
      request_qty: 1200,
      uom: 'Cái',
      proposed_price: 9500,
      src_pr_item_id: 501,
    },
    {
      received_date: '',
      result_due_date: '',
      item_group: '',
      requirement_detail: 'Băng keo',
      other_requirement: '',
      request_qty: 0,
      uom: '',
      proposed_price: 0,
      src_pr_item_id: 0,
    },
  ],
}

function emptySurveyRequest(): SurveyRequestDetail {
  return {
    id: 0,
    code: '',
    company_id: 9,
    requester: 'Người lập',
    requester_id: 5,
    requester_position: 'NV',
    department_id: 12,
    department: 'Phòng của người lập',
    head_of_dept_id: 8,
    head_of_dept: 'TBP của người lập',
    handler_dept_id: 0,
    purpose: '',
    request_date: '2026-11-09',
    status: 'draft',
    note: '',
    reject_reason: '',
    created_at: '2026-11-09T00:00:00Z',
    created_by: 5,
    lines: [],
  }
}

/**
 * duoc-CR-741 — màn tạo YCBG đọc `state.fromPr` như bản v1 (`SurveyRequestDetail.tsx` ~:112-130).
 * Gói đi qua lịch sử trình duyệt nên phải đọc phòng thủ; dòng phải giữ `src_pr_item_id` vì backend
 * dùng nó để kéo ảnh của dòng YCMH nguồn sang lúc Lưu (`edit_service.py`).
 */
describe('parseSurveyRequestFromPurchaseRequest', () => {
  it('reads the package built by the purchase request button unchanged', () => {
    //  Gói cũ (trước rà mã CR-741) không có id phòng / TBP — đọc ra 0, không vỡ.
    expect(parseSurveyRequestFromPurchaseRequest(FROM_PR)).toEqual({
      ...FROM_PR,
      handler_dept_id: 0,
      department_id: 0,
      head_of_dept_id: 0,
    })
  })

  it('reads the source department and head ids when the package carries them', () => {
    const parsed = parseSurveyRequestFromPurchaseRequest({ ...FROM_PR, department_id: 31, head_of_dept_id: 44 })
    expect(parsed).toMatchObject({ department_id: 31, head_of_dept_id: 44 })
  })

  it('keeps the handling department v1 also reads when the package carries one', () => {
    expect(parseSurveyRequestFromPurchaseRequest({ ...FROM_PR, handler_dept_id: 14 })?.handler_dept_id).toBe(14)
  })

  it('returns null for anything that is not a package with a source code', () => {
    expect(parseSurveyRequestFromPurchaseRequest(undefined)).toBeNull()
    expect(parseSurveyRequestFromPurchaseRequest(null)).toBeNull()
    expect(parseSurveyRequestFromPurchaseRequest('PYC26110901')).toBeNull()
    expect(parseSurveyRequestFromPurchaseRequest({ ...FROM_PR, pr_code: '   ' })).toBeNull()
  })

  it('drops broken lines and coerces bad numbers to 0 instead of breaking the page', () => {
    const parsed = parseSurveyRequestFromPurchaseRequest({
      ...FROM_PR,
      pr_id: 'abc',
      lines: [null, 'x', { requirement_detail: 'Nắp', request_qty: -5, src_pr_item_id: 'NaN' }],
    })
    expect(parsed?.pr_id).toBe(0)
    expect(parsed?.lines).toHaveLength(1)
    expect(parsed?.lines[0]).toMatchObject({ requirement_detail: 'Nắp', request_qty: 0, src_pr_item_id: 0 })
  })

  it('treats a missing lines field as no lines', () => {
    expect(parseSurveyRequestFromPurchaseRequest({ ...FROM_PR, lines: undefined })?.lines).toEqual([])
  })
})

describe('applySurveyRequestFromPurchaseRequest', () => {
  const parsed = parseSurveyRequestFromPurchaseRequest(FROM_PR)
  if (!parsed) throw new Error('fixture must parse')

  it('fills requester, department, head of department, company, purpose like v1', () => {
    const filled = applySurveyRequestFromPurchaseRequest(emptySurveyRequest(), parsed)
    expect(filled).toMatchObject({
      company_id: 3,
      requester: 'Nguyễn Văn A',
      requester_id: 77,
      requester_position: 'Chuyên viên',
      department: 'Marketing',
      head_of_dept: 'Trần Thị B',
      purpose: 'Mua thùng cho đợt hàng Tết',
    })
    //  Id phòng / TBP của NGƯỜI LẬP không được dính sang phiếu của người yêu cầu khác.
    expect(filled.department_id).toBe(0)
    expect(filled.head_of_dept_id).toBe(0)
  })

  it('keeps the source department id and head id, not the profile ones (review duoc-CR-741)', () => {
    const filled = applySurveyRequestFromPurchaseRequest(emptySurveyRequest(), {
      ...parsed,
      department_id: 31,
      head_of_dept_id: 44,
    })
    expect(filled).toMatchObject({
      department_id: 31,
      department: 'Marketing',
      head_of_dept_id: 44,
      head_of_dept: 'Trần Thị B',
    })
  })

  it('appends the v1 trace (Tạo từ YCMH <mã>) under the source note', () => {
    expect(applySurveyRequestFromPurchaseRequest(emptySurveyRequest(), parsed).note).toBe(
      'Cần gấp\n(Tạo từ YCMH PYC26110901)',
    )
    const noNote = applySurveyRequestFromPurchaseRequest(emptySurveyRequest(), { ...parsed, note: '' })
    expect(noNote.note).toBe('(Tạo từ YCMH PYC26110901)')
  })

  it('keeps src_pr_item_id on every line so the backend can pull the source images', () => {
    const filled = applySurveyRequestFromPurchaseRequest(emptySurveyRequest(), parsed)
    expect(filled.lines).toHaveLength(2)
    expect(filled.lines[0]).toMatchObject({
      requirement_detail: 'Thùng carton — 5 lớp',
      item_group: 'Bao bì',
      request_qty: 1200,
      result_due_date: '2026-11-20',
      src_pr_item_id: 501,
      //  Trường phụ của dòng dựng từ dòng rỗng — thiếu là bảng dòng đọc `undefined`.
      assignee: '',
      progress_tone: 'gray',
    })
    expect(filled.lines[1]).toMatchObject({ src_pr_item_id: 0 })
  })

  it('ticks Nhờ phòng khác xử lý only when the source had a handling department', () => {
    expect(applySurveyRequestFromPurchaseRequest(emptySurveyRequest(), parsed).handler_dept_assigned).toBe(false)
    const withDept = applySurveyRequestFromPurchaseRequest(emptySurveyRequest(), {
      ...parsed,
      handler_dept_id: 14,
    })
    expect(withDept).toMatchObject({ handler_dept_id: 14, handler_dept_assigned: true })
  })

  it('keeps the creator company when the source has none, so the company picker is not blank', () => {
    expect(
      applySurveyRequestFromPurchaseRequest(emptySurveyRequest(), { ...parsed, company_id: 0 }).company_id,
    ).toBe(9)
  })
})

/**
 * Rà mã duoc-CR-741: nhịp bù phòng CR-086 của màn tạo YCBG ghi đè phòng của YCMH bằng phòng
 * hiện tại trong hồ sơ người yêu cầu. Gói có tên phòng thì phải giữ, chỉ phiếu thường mới bù.
 */
describe('keepsSourceDepartment', () => {
  const parsed = parseSurveyRequestFromPurchaseRequest(FROM_PR)
  if (!parsed) throw new Error('fixture must parse')

  it('keeps the purchase request department when the package names one', () => {
    expect(keepsSourceDepartment(parsed)).toBe(true)
  })

  it('lets the profile fill the department for a plain new ticket or a nameless package', () => {
    expect(keepsSourceDepartment(null)).toBe(false)
    expect(keepsSourceDepartment({ ...parsed, department: '' })).toBe(false)
    expect(keepsSourceDepartment({ ...parsed, department: '   ' })).toBe(false)
  })
})
