import { describe, expect, it } from 'vitest'

import { LEAVE_STATUS } from './leave'
import {
  encashmentYearOptions,
  formatEncashDays,
  getLeaveEncashmentActions,
  isPayoutRejected,
  LEAVE_ENCASHMENT_REASON,
  LEAVE_ENCASHMENT_REASON_LABELS,
  LEAVE_ENCASHMENT_STATUS,
  LEAVE_ENCASHMENT_STATUS_LABELS,
  validateEncashmentDays,
} from './leave-encashment'

const ALL = { write: true, delete: true, approve: true, cancel: true }
const NONE = { write: false, delete: false, approve: false, cancel: false }

describe('leave encashment code sets', () => {
  it('mirrors backend LeaveEncashmentStatus 1..6 and shares numbers with leave requests (one badge for both)', () => {
    expect(Object.values(LEAVE_ENCASHMENT_STATUS)).toEqual([1, 2, 3, 4, 5, 6])
    expect(LEAVE_ENCASHMENT_STATUS.APPROVED).toBe(LEAVE_STATUS.APPROVED)
    expect(LEAVE_ENCASHMENT_STATUS.CANCELLED).toBe(LEAVE_STATUS.CANCELLED)
    for (const code of Object.values(LEAVE_ENCASHMENT_STATUS)) {
      expect(LEAVE_ENCASHMENT_STATUS_LABELS[code]).toBeTruthy()
    }
  })

  it('has exactly the two reasons of D5 with labels', () => {
    expect(LEAVE_ENCASHMENT_REASON).toEqual({ YEAR_END: 1, RESIGNATION: 2 })
    expect(Object.keys(LEAVE_ENCASHMENT_REASON_LABELS)).toHaveLength(2)
  })
})

describe('getLeaveEncashmentActions', () => {
  const at = (status: number, extra: { approval_instance_id?: number; cancel_blocked_reason?: string } = {}) => ({
    status,
    approval_instance_id: extra.approval_instance_id ?? 0,
    cancel_blocked_reason: extra.cancel_blocked_reason,
  })

  it('returns nothing while the record is still loading', () => {
    expect(Object.values(getLeaveEncashmentActions(undefined, ALL)).some(Boolean)).toBe(false)
  })

  it('draft: edit + submit + delete, but no cancel (draft is deleted, not cancelled)', () => {
    const a = getLeaveEncashmentActions(at(LEAVE_ENCASHMENT_STATUS.DRAFT), ALL)
    expect(a).toMatchObject({ edit: true, submit: true, remove: true, cancel: false, directDecision: false })
  })

  it('returned: editable again and cancellable, but not deletable (backend deletes drafts only)', () => {
    const a = getLeaveEncashmentActions(at(LEAVE_ENCASHMENT_STATUS.RETURNED), ALL)
    expect(a).toMatchObject({ edit: true, submit: true, remove: false, cancel: true })
  })

  it('pending without a running flow offers direct approve; with a flow only the engine buttons', () => {
    expect(getLeaveEncashmentActions(at(LEAVE_ENCASHMENT_STATUS.PENDING), ALL)).toMatchObject({
      directDecision: true,
      engineDecision: false,
    })
    expect(
      getLeaveEncashmentActions(at(LEAVE_ENCASHMENT_STATUS.PENDING, { approval_instance_id: 9 }), ALL),
    ).toMatchObject({ directDecision: false, engineDecision: true })
  })

  it('pending without a flow hides direct approve on the viewer\'s own request (self-approval is always blocked)', () => {
    expect(
      getLeaveEncashmentActions(at(LEAVE_ENCASHMENT_STATUS.PENDING), { ...ALL, isOwnRequest: true }),
    ).toMatchObject({ directDecision: false, cancel: true })
  })

  it('approved: cancel only while the YCTT does not block it (D7a)', () => {
    expect(getLeaveEncashmentActions(at(LEAVE_ENCASHMENT_STATUS.APPROVED), ALL).cancel).toBe(true)
    const blocked = at(LEAVE_ENCASHMENT_STATUS.APPROVED, {
      cancel_blocked_reason: 'YCTT YCTT00012 đang ở Chờ duyệt — kế toán từ chối YCTT trước',
    })
    expect(getLeaveEncashmentActions(blocked, ALL).cancel).toBe(false)
    //  Khoảng trắng do backend không được coi là "có lý do chặn".
    expect(getLeaveEncashmentActions(at(LEAVE_ENCASHMENT_STATUS.APPROVED, { cancel_blocked_reason: '  ' }), ALL).cancel).toBe(true)
  })

  it('rejected and cancelled are terminal: no button at all', () => {
    for (const status of [LEAVE_ENCASHMENT_STATUS.REJECTED, LEAVE_ENCASHMENT_STATUS.CANCELLED]) {
      expect(Object.values(getLeaveEncashmentActions(at(status), ALL)).some(Boolean)).toBe(false)
    }
  })

  it('without permissions nothing but the engine buttons (those follow the task, not the role)', () => {
    expect(getLeaveEncashmentActions(at(LEAVE_ENCASHMENT_STATUS.DRAFT), NONE)).toMatchObject({
      edit: false,
      submit: false,
      remove: false,
    })
    expect(
      getLeaveEncashmentActions(at(LEAVE_ENCASHMENT_STATUS.PENDING, { approval_instance_id: 3 }), NONE)
        .engineDecision,
    ).toBe(true)
  })
})

describe('isPayoutRejected', () => {
  it('is true only for an approved encashment whose YCTT was rejected by accounting', () => {
    expect(isPayoutRejected({ status: LEAVE_ENCASHMENT_STATUS.APPROVED, payment_status: 'cancelled' })).toBe(true)
    expect(isPayoutRejected({ status: LEAVE_ENCASHMENT_STATUS.APPROVED, payment_status: 'draft' })).toBe(false)
    expect(isPayoutRejected({ status: LEAVE_ENCASHMENT_STATUS.CANCELLED, payment_status: 'cancelled' })).toBe(false)
    expect(isPayoutRejected({ status: LEAVE_ENCASHMENT_STATUS.APPROVED, payment_status: '' })).toBe(false)
    expect(isPayoutRejected(undefined)).toBe(false)
  })
})

describe('validateEncashmentDays', () => {
  it('rejects zero, negatives and NaN', () => {
    expect(validateEncashmentDays(0, 5)).not.toBe('')
    expect(validateEncashmentDays(-1, 5)).not.toBe('')
    expect(validateEncashmentDays(Number.NaN, 5)).not.toBe('')
  })

  it('only accepts half-day steps', () => {
    expect(validateEncashmentDays(0.5, 5)).toBe('')
    expect(validateEncashmentDays(2.25, 5)).toMatch(/0,5/)
  })

  it('caps at the encashable maximum, but no cap when the maximum is unknown', () => {
    expect(validateEncashmentDays(6, 6)).toBe('')
    expect(validateEncashmentDays(6.5, 6)).toMatch(/tối đa 6 ngày/)
    expect(validateEncashmentDays(0.5, 0)).toMatch(/tối đa 0 ngày/)
    expect(validateEncashmentDays(300, null)).toBe('')
  })
})

describe('helpers', () => {
  it('offers this year and last year only (D9)', () => {
    expect(encashmentYearOptions(new Date(2026, 10, 3))).toEqual([2026, 2025])
    expect(encashmentYearOptions(new Date(2027, 0, 1))).toEqual([2027, 2026])
  })

  it('formats days with a Vietnamese decimal comma and no float drift', () => {
    expect(formatEncashDays(1.5)).toBe('1,5')
    expect(formatEncashDays(6)).toBe('6')
    expect(formatEncashDays(0.1 + 0.2)).toBe('0,3')
    expect(formatEncashDays(Number.NaN)).toBe('0')
  })
})
