import { describe, expect, it } from 'vitest'

import { emptyDocumentForm } from './document-form-defaults'

describe('emptyDocumentForm', () => {
  //  Yêu cầu người dùng 24/08/2026: bốn ô này suy thẳng từ tài khoản đang đăng
  //  nhập, đừng bắt chọn lại thứ hệ đã biết.
  it('tự điền pháp nhân, phòng ban, người chịu trách nhiệm và người soạn theo tài khoản', () => {
    const form = emptyDocumentForm({ company_id: 1, department_id: 5, employee_id: 94 })

    expect(form.company_id).toBe(1)
    expect(form.department_id).toBe(5)
    expect(form.owner_employee_id).toBe(94)
    expect(form.drafter_employee_id).toBe(94)
  })

  it('tài khoản chưa gắn hồ sơ nhân sự thì để TRỐNG, không điền bừa số 0 hợp lệ', () => {
    const form = emptyDocumentForm()

    expect(form.company_id).toBe(0)
    expect(form.department_id).toBe(0)
    expect(form.owner_employee_id).toBe(0)
    expect(form.drafter_employee_id).toBeNull()
  })

  it('mức mật mặc định là 2 (Nội bộ), không phải 0 — 0 nằm ngoài dải hợp lệ', () => {
    expect(emptyDocumentForm().secrecy_level).toBe(2)
  })

  it('ngày hiệu lực để TRỐNG — đó là quyết định nghiệp vụ, không điền hộ', () => {
    expect(emptyDocumentForm().effective_date).toBe('')
  })
})
