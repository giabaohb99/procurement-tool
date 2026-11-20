import { describe, expect, it } from 'vitest'

import {
  joinPackagingWarnings,
  normalizeWarnings,
  packagingRoleLabel,
  packagingWarningText,
} from './packaging-warning-text'

//  Dùng mã KHÔNG có trong bộ (900+) để bài kiểm không phụ thuộc nhãn tiếng Việt của backend: đổi câu
//  nhãn bên đó không làm đỏ ở đây, còn luật ghép (dự phòng, kèm vai trò, bỏ trùng) thì vẫn bị canh.
describe('packaging warning text', () => {
  it('falls back to "Mã n" instead of a blank note when the code set lacks the code', () => {
    expect(packagingWarningText({ kind: 901 })).toBe('Mã 901')
    expect(packagingRoleLabel(902)).toBe('Mã 902')
  })

  it('appends the component role after a colon when the warning names one', () => {
    expect(packagingWarningText({ kind: 901, role: 902 })).toBe('Mã 901: Mã 902')
  })

  it('accepts both bare codes and {kind, role} objects from the server', () => {
    expect(normalizeWarnings([901, { kind: 903, role: null }])).toEqual([
      { kind: 901 },
      { kind: 903, role: null },
    ])
  })

  it('joins with "; " and drops duplicates', () => {
    expect(joinPackagingWarnings([901, { kind: 901 }, { kind: 903 }])).toBe('Mã 901; Mã 903')
  })

  it('reads labels from the generated code sets (role 2 + warning 3 = component price missing on the cap)', () => {
    //  Canh nối giữa số vai trò của định mức (`PACKAGING_PART_COLUMNS`) và bộ mã sinh từ backend:
    //  backend đổi số vai trò thì câu ghi chú sẽ nói sai thành phần — bài này đỏ trước.
    expect(packagingRoleLabel(2)).toBe('Nắp')
    expect(packagingRoleLabel(5)).toBe('Thùng')
    expect(packagingWarningText({ kind: 3, role: 2 })).toMatch(/: Nắp$/)
  })

  it('returns an empty note for null, undefined or an empty list', () => {
    expect(joinPackagingWarnings(null)).toBe('')
    expect(joinPackagingWarnings(undefined)).toBe('')
    expect(joinPackagingWarnings([])).toBe('')
    expect(packagingRoleLabel(null)).toBe('')
  })
})
