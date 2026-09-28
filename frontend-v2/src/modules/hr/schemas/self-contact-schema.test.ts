import { describe, expect, it } from 'vitest'

import {
  selfContactSchema,
  toSelfContactFormValues,
  toSelfContactPayload,
  type SelfContactFormValues,
} from './self-contact-schema'

/**
 * Form tự sửa liên hệ ở Trang cá nhân (bao-CR-508).
 *
 * Backend khai `extra="forbid"` cho cửa này: MỘT khóa thừa là cả lần lưu ăn
 * 422. Nên chỗ đáng kiểm nhất là thân gửi lên không bao giờ mang khóa lạ, kể cả
 * khi form bị truyền nhầm nguyên object hồ sơ.
 */
describe('toSelfContactPayload', () => {
  it('sends exactly the three contact keys even when the values carry extra fields', () => {
    //  Kịch bản thật: ai đó truyền nguyên object hồ sơ vào thay cho giá trị form.
    const polluted = {
      phone: '0901',
      permanent_address: 'A',
      current_address: 'B',
      department_id: 9,
      bank_account_no: '123',
      company_id: 3,
      id: 77,
    } as unknown as SelfContactFormValues

    const payload = toSelfContactPayload(polluted)

    expect(Object.keys(payload).sort()).toEqual(['current_address', 'permanent_address', 'phone'])
  })

  it('trims surrounding whitespace so pasted numbers do not carry spaces', () => {
    expect(
      toSelfContactPayload({ phone: '  0987 ', permanent_address: ' Huế ', current_address: '' }),
    ).toEqual({ phone: '0987', permanent_address: 'Huế', current_address: '' })
  })

  it('keeps an emptied field as an empty string so the backend clears it', () => {
    expect(toSelfContactPayload({ phone: '   ', permanent_address: '', current_address: '' }).phone).toBe('')
  })
})

describe('toSelfContactFormValues', () => {
  it('turns missing addresses into empty strings instead of undefined inputs', () => {
    //  Hồ sơ cũ chưa có hai cột địa chỉ trả `undefined` — ô nhập nhận `undefined`
    //  là chuyển từ không-kiểm-soát sang có-kiểm-soát và React cảnh báo.
    expect(toSelfContactFormValues({ phone: '0901' })).toEqual({
      phone: '0901',
      permanent_address: '',
      current_address: '',
    })
  })
})

describe('selfContactSchema length limits match the backend columns', () => {
  const base = { phone: '', permanent_address: '', current_address: '' }

  it.each([
    ['phone', 25],
    ['permanent_address', 500],
    ['current_address', 500],
  ] as const)('accepts %s at exactly %i characters and rejects one more', (field, limit) => {
    expect(selfContactSchema.safeParse({ ...base, [field]: 'x'.repeat(limit) }).success).toBe(true)
    const tooLong = selfContactSchema.safeParse({ ...base, [field]: 'x'.repeat(limit + 1) })
    expect(tooLong.success).toBe(false)
  })

  it('does not count surrounding spaces against the limit', () => {
    expect(selfContactSchema.safeParse({ ...base, phone: `  ${'1'.repeat(25)}  ` }).success).toBe(true)
  })
})
