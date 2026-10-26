import { describe, expect, it } from 'vitest'

import type { BookingPickOptions } from '../types/vehicle-booking'
import {
  approverSelectOptions,
  companySelectOptions,
  initialCompanyId,
  pickValidationMessage,
} from './booking-pick-options'

const DATA: BookingPickOptions = {
  companies: [
    { id: 3, name: 'Dego Holding', short_name: 'DGH', tax_code: '0312345678', logo: '/logo-3.png' },
    { id: 5, name: 'Công ty con', short_name: '', tax_code: '', logo: '' },
  ],
  approvers: [
    {
      user_id: 40,
      employee_id: 400,
      code: 'NSU100',
      name: 'Trần Điều Phối',
      avatar: '/a-40.png',
      roles: [{ role: 'Điều phối viên (Đặt xe)', scope: 'company', scope_label: 'Công ty' }],
    },
  ],
  default_company_id: 3,
}

describe('companySelectOptions', () => {
  it('shows the company name with its logo, tax code as the muted hint', () => {
    expect(companySelectOptions(DATA, 0, '')).toEqual([
      { value: '3', label: 'Dego Holding', hint: 'MST 0312345678', avatar: '/logo-3.png' },
      { value: '5', label: 'Công ty con', hint: '', avatar: '' },
    ])
  })

  it('keeps a saved company that is no longer active so the field never reads blank', () => {
    expect(companySelectOptions(DATA, 9, 'Công ty cũ').at(-1)).toEqual({
      value: '9',
      label: 'Công ty cũ (đã ngừng dùng)',
      avatar: '',
    })
    expect(companySelectOptions(undefined, 9, '').at(-1)?.label).toBe('Công ty #9 (đã ngừng dùng)')
  })
})

describe('approverSelectOptions', () => {
  it('shows avatar + «code - name», with the role (scope) granting approval as the hint', () => {
    expect(approverSelectOptions(DATA, 0, '')).toEqual([
      {
        value: '40',
        label: 'NSU100 - Trần Điều Phối',
        hint: 'Điều phối viên (Đặt xe) (Công ty)',
        avatar: '/a-40.png',
      },
    ])
  })

  it('flags a saved approver who lost the permission instead of silently dropping them', () => {
    expect(approverSelectOptions(DATA, 77, 'Lê Cũ').at(-1)).toEqual({
      value: '77',
      label: 'Lê Cũ (không còn quyền duyệt — chọn lại)',
      avatar: '',
    })
  })

  it('drops the current user so nobody is offered themselves and then blocked with a 422', () => {
    expect(approverSelectOptions(DATA, 0, '', 40)).toEqual([])
    expect(approverSelectOptions(DATA, 0, '', 999)).toHaveLength(1)
  })

  it('does not invent a stale entry while the list is still loading', () => {
    expect(approverSelectOptions(undefined, 77, 'Lê Cũ')).toEqual([])
  })
})

describe('initialCompanyId', () => {
  it('prefers the company already on the booking, then the creator company, then nothing', () => {
    expect(initialCompanyId(5, DATA)).toBe(5)
    expect(initialCompanyId(0, DATA)).toBe(3)
    expect(initialCompanyId(undefined, DATA)).toBe(3)
    expect(initialCompanyId(undefined, undefined)).toBe(0)
    expect(initialCompanyId(0, { ...DATA, default_company_id: 0 })).toBe(0)
  })
})

describe('pickValidationMessage', () => {
  it('requires a company and an approver before submitting', () => {
    expect(pickValidationMessage(DATA, 0, 40)).toBe('Vui lòng chọn công ty.')
    expect(pickValidationMessage(DATA, 3, 0)).toBe('Vui lòng chọn người phê duyệt.')
  })

  it('blocks an approver who is no longer in the list, as the backend would with 422', () => {
    expect(pickValidationMessage(DATA, 3, 77)).toMatch(/không còn quyền duyệt/)
    expect(pickValidationMessage({ ...DATA, approvers: [] }, 3, 40)).toMatch(/không còn quyền duyệt/)
  })

  it('passes a valid pair and does not block while the list is still loading', () => {
    expect(pickValidationMessage(DATA, 3, 40)).toBe('')
    expect(pickValidationMessage(undefined, 3, 40)).toBe('')
  })
})
