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
  it('sends exactly the four contact keys even when the values carry extra fields', () => {
    //  Kịch bản thật: ai đó truyền nguyên object hồ sơ vào thay cho giá trị form.
    const polluted = {
      phone: '0901',
      phone_label: '',
      extra_phones: [],
      permanent_address: 'A',
      current_address: 'B',
      department_id: 9,
      bank_account_no: '123',
      company_id: 3,
      id: 77,
    } as unknown as SelfContactFormValues

    const payload = toSelfContactPayload(polluted)

    expect(Object.keys(payload).sort()).toEqual(['current_address', 'extra_phones', 'permanent_address', 'phone', 'phone_label'])
  })

  it('trims surrounding whitespace so pasted numbers do not carry spaces', () => {
    expect(
      toSelfContactPayload({ phone: '  0987 ', phone_label: ' Zalo ', extra_phones: [], permanent_address: ' Huế ', current_address: '' }),
    ).toEqual({ phone: '0987', phone_label: 'Zalo', extra_phones: [], permanent_address: 'Huế', current_address: '' })
  })

  it('keeps an emptied field as an empty string so the backend clears it', () => {
    expect(toSelfContactPayload({ phone: '   ', phone_label: '', extra_phones: [], permanent_address: '', current_address: '' }).phone).toBe('')
  })
})

describe('toSelfContactFormValues', () => {
  it('turns missing addresses into empty strings instead of undefined inputs', () => {
    //  Hồ sơ cũ chưa có hai cột địa chỉ trả `undefined` — ô nhập nhận `undefined`
    //  là chuyển từ không-kiểm-soát sang có-kiểm-soát và React cảnh báo.
    expect(toSelfContactFormValues({ phone: '0901' })).toEqual({
      phone: '0901',
      phone_label: '',
      extra_phones: [],
      permanent_address: '',
      current_address: '',
    })
  })
})

describe('selfContactSchema length limits match the backend columns', () => {
  const base = { phone: '', phone_label: '', extra_phones: [], permanent_address: '', current_address: '' }

  it.each([
    ['phone', 25],
    ['phone_label', 50],
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

describe('số điện thoại khác (duoc-CR-694)', () => {
  const base = { phone: '0901000111', phone_label: '', permanent_address: '', current_address: '' }

  it('bỏ dòng trống số và cắt khoảng trắng khi dựng thân PATCH', () => {
    const payload = toSelfContactPayload({
      ...base,
      extra_phones: [
        { number: ' 0912 345 678 ', label: ' Zalo ' },
        { number: '  ', label: 'bỏ' },
      ],
    })
    expect(payload.extra_phones).toEqual([{ number: '0912 345 678', label: 'Zalo' }])
  })

  it('chặn số sai định dạng, số trùng nhau và số trùng số chính', () => {
    const run = (extra_phones: { number: string; label: string }[]) =>
      selfContactSchema.safeParse({ ...base, extra_phones }).success
    expect(run([{ number: 'abc12345678', label: '' }])).toBe(false)
    expect(run([{ number: '123', label: '' }])).toBe(false)
    expect(run([{ number: '0912345678', label: '' }, { number: '0912.345.678', label: '' }])).toBe(false)
    expect(run([{ number: '0901 000 111', label: '' }])).toBe(false)
    expect(run([{ number: '0912345678', label: 'Zalo' }])).toBe(true)
  })

  it('tối đa 4 số khác', () => {
    const five = Array.from({ length: 5 }, (_, i) => ({ number: `091234567${i}`, label: '' }))
    expect(selfContactSchema.safeParse({ ...base, extra_phones: five }).success).toBe(false)
    expect(selfContactSchema.safeParse({ ...base, extra_phones: five.slice(0, 4) }).success).toBe(true)
  })
})
