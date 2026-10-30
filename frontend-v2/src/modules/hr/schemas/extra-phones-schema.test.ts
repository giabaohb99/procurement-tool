import { describe, expect, it } from 'vitest'

import {
  cleanExtraPhones,
  duplicatePhoneIndexes,
  phoneNumberError,
  sameExtraPhones,
  swapWithMain,
} from './extra-phones-schema'
import {
  EMPTY_EMPLOYEE_PROFILE_FORM,
  employeeProfileFormValues,
  employeeProfileSchema,
  pickWritableProfile,
} from './employee-schema'
import type { Employee } from '../types/employee'

describe('phoneNumberError', () => {
  it('chấp nhận số có ký tự phân cách và đủ 8-15 chữ số', () => {
    expect(phoneNumberError('+84 (28) 3822-1234')).toBeNull()
    expect(phoneNumberError('')).toBeNull()
  })
  it('từ chối chữ, quá ngắn, quá dài, quá 20 ký tự', () => {
    expect(phoneNumberError('09a1234567')).not.toBeNull()
    expect(phoneNumberError('1234567')).not.toBeNull()
    expect(phoneNumberError('1234567890123456')).not.toBeNull()
    expect(phoneNumberError('0'.repeat(21))).not.toBeNull()
  })
})

describe('swapWithMain', () => {
  it('hoán đổi CẢ số lẫn nhãn giữa số chính và số phụ', () => {
    const out = swapWithMain(
      { number: '0911111111', label: 'Cá nhân' },
      [{ number: '0922222222', label: 'Zalo' }],
      0,
    )
    expect(out.main).toEqual({ number: '0922222222', label: 'Zalo' })
    expect(out.extras).toEqual([{ number: '0911111111', label: 'Cá nhân' }])
  })
  it('chỉ số lạ thì giữ nguyên', () => {
    const main = { number: '0911111111', label: '' }
    expect(swapWithMain(main, [], 3)).toEqual({ main, extras: [] })
  })
})

describe('trùng số', () => {
  it('so sau khi bỏ ký tự phân cách, gồm cả số chính', () => {
    const dup = duplicatePhoneIndexes('0911 111 111', [
      { number: '0911.111.111', label: '' },
      { number: '0922222222', label: '' },
      { number: '0922 222 222', label: '' },
    ])
    expect([...dup]).toEqual([0, 2])
  })
})

describe('so sánh / làm sạch', () => {
  it('bỏ dòng trống và coi hai danh sách giống nhau khi chỉ khác dòng trống', () => {
    expect(cleanExtraPhones([{ number: ' ', label: 'x' }])).toEqual([])
    expect(sameExtraPhones([{ number: '0922222222', label: '' }, { number: '', label: '' }], [{ number: '0922222222', label: '' }])).toBe(true)
    expect(sameExtraPhones(undefined, [])).toBe(true)
    expect(sameExtraPhones([{ number: '0922222222', label: 'A' }], [{ number: '0922222222', label: 'B' }])).toBe(false)
  })
})

describe('form hồ sơ', () => {
  const saved = [{ number: '0922222222', label: 'Zalo' }]

  it('không gửi extra_phones khi không đổi, gửi bản sạch khi đổi', () => {
    const same = pickWritableProfile({ ...EMPTY_EMPLOYEE_PROFILE_FORM, extra_phones: saved }, true, saved)
    expect('extra_phones' in same).toBe(false)
    const changed = pickWritableProfile(
      { ...EMPTY_EMPLOYEE_PROFILE_FORM, extra_phones: [...saved, { number: ' 0933333333 ', label: '' }, { number: '', label: '' }] },
      true,
      saved,
    )
    expect(changed.extra_phones).toEqual([...saved, { number: '0933333333', label: '' }])
  })

  it('xóa hết số phụ đã lưu thì gửi []', () => {
    const out = pickWritableProfile({ ...EMPTY_EMPLOYEE_PROFILE_FORM, extra_phones: [] }, true, saved)
    expect(out.extra_phones).toEqual([])
  })

  it('hồ sơ chưa có khóa extra_phones nạp thành []', () => {
    expect(employeeProfileFormValues({ id: 1, phone: '' } as Employee).extra_phones).toEqual([])
  })

  it('schema chặn số phụ trùng số chính và báo lỗi ở extra_phones', () => {
    const r = employeeProfileSchema.safeParse({
      ...EMPTY_EMPLOYEE_PROFILE_FORM,
      full_name: 'A',
      phone: '0911111111',
      extra_phones: [{ number: '0911 111 111', label: '' }],
    })
    expect(r.success).toBe(false)
    if (!r.success) expect(r.error.issues[0].path).toEqual(['extra_phones'])
  })
})
