import { describe, expect, it } from 'vitest'

import { companySchema, EMPTY_COMPANY_FORM } from '../schemas/company-schema'
import { COMPANY_TYPE, COMPANY_TYPE_LABELS, COMPANY_TYPE_OPTIONS } from './company'

// bao-CR-531: bộ mã «Loại hình» gõ tay theo `backend/app/modules/company/constants.py`
// (CompanyType: COMPANY = 1, HOUSEHOLD = 2). Đổi số ở backend mà quên bên này là bản in
// của hộ kinh doanh ra bốn ô ký có tên như công ty.
describe('company type code set', () => {
  it('matches the backend numbers exactly', () => {
    expect(COMPANY_TYPE).toEqual({ COMPANY: 1, HOUSEHOLD: 2 })
    expect(COMPANY_TYPE_OPTIONS).toEqual([
      { id: 1, label: 'Công ty' },
      { id: 2, label: 'Hộ kinh doanh' },
    ])
    expect(Object.keys(COMPANY_TYPE_LABELS)).toHaveLength(2)
  })

  it('defaults a new company form to «Công ty»', () => {
    expect(EMPTY_COMPANY_FORM.company_type).toBe(COMPANY_TYPE.COMPANY)
  })

  it.each([0, 3, -1, 1.5])('rejects unknown code %s', (value) => {
    const result = companySchema.safeParse({ ...EMPTY_COMPANY_FORM, name: 'A', company_type: value })
    expect(result.success).toBe(false)
  })

  it('accepts household', () => {
    const result = companySchema.safeParse({ ...EMPTY_COMPANY_FORM, name: 'A', company_type: 2 })
    expect(result.success).toBe(true)
  })
})
