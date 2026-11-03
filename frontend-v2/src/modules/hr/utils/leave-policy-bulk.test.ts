import { describe, expect, it } from 'vitest'

import type { PolicyPreviewItem } from '../types/leave-policy'
import {
  buildBulkPreviewPayload,
  bulkPreviewSignature,
  createBulkSettings,
  selectableEmployeeIds,
  validateBulkSettings,
} from './leave-policy-bulk'
import { FILTER_ANY } from './employee-filter-id'

const base = { ...createBulkSettings('2026-11-03'), policyId: 5 }

describe('buildBulkPreviewPayload', () => {
  it('omits every "any" filter and sends an open range as null', () => {
    expect(buildBulkPreviewPayload(base)).toEqual({
      policy_id: 5,
      effective_from: '2026-11-03',
      effective_to: null,
      close_previous: false,
      only_without_active: true,
    })
  })

  it('sends chosen filters as numbers and drops 0 / garbage / negative (backend requires >= 1)', () => {
    const payload = buildBulkPreviewPayload({
      ...base,
      companyId: '2',
      departmentId: '0',
      employmentType: 'abc',
      jobLevel: '-3',
      to: '2026-12-31',
      closePrevious: true,
      onlyWithoutActive: false,
    })
    expect(payload).toEqual({
      policy_id: 5,
      effective_from: '2026-11-03',
      effective_to: '2026-12-31',
      close_previous: true,
      only_without_active: false,
      company_id: 2,
    })
  })
})

describe('bulkPreviewSignature', () => {
  it('ignores the recalc tick (it does not change the preview) but changes on any filter / date / policy', () => {
    const sig = bulkPreviewSignature(base)
    expect(bulkPreviewSignature({ ...base, recalc: false })).toBe(sig)
    expect(bulkPreviewSignature({ ...base, policyId: 6 })).not.toBe(sig)
    expect(bulkPreviewSignature({ ...base, to: '2026-12-31' })).not.toBe(sig)
    expect(bulkPreviewSignature({ ...base, jobLevel: '3' })).not.toBe(sig)
    expect(bulkPreviewSignature({ ...base, closePrevious: true })).not.toBe(sig)
    //  "any" và id rác cùng nghĩa "không lọc" → cùng chữ ký, khỏi bắt xem lại vô cớ.
    expect(bulkPreviewSignature({ ...base, jobLevel: 'x' })).toBe(bulkPreviewSignature({ ...base, jobLevel: FILTER_ANY }))
  })
})

describe('validateBulkSettings', () => {
  it('requires a policy and a start date, and rejects a reversed range', () => {
    expect(validateBulkSettings({ ...base, policyId: 0 })).toBe('Chọn chính sách.')
    expect(validateBulkSettings({ ...base, from: '' })).toBe('Chọn "Từ ngày".')
    expect(validateBulkSettings({ ...base, to: '2026-11-02' })).toMatch(/không được trước/)
    expect(validateBulkSettings({ ...base, to: '2026-11-03' })).toBe('')
  })
})

describe('selectableEmployeeIds', () => {
  const item = (id: number, conflict: PolicyPreviewItem['conflict']): PolicyPreviewItem => ({
    employee_id: id,
    code: `NV${id}`,
    name: `Người ${id}`,
    department_name: '',
    hire_date: null,
    current: null,
    conflict,
    conflict_message: '',
    changes: [],
  })

  it('keeps only rows without any conflict, in order', () => {
    expect(
      selectableEmployeeIds([item(1, null), item(2, 'overlap'), item(3, 'self'), item(4, 'inactive'), item(5, null)]),
    ).toEqual([1, 5])
    expect(selectableEmployeeIds([])).toEqual([])
  })
})
