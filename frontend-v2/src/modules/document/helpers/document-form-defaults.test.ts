import { describe, expect, it } from 'vitest'

import { documentToForm, emptyDocumentForm, formToPayload } from './document-form-defaults'
import type { DocumentRecord } from '../types/document-record'

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

/**
 * LƯU LẠI GIẤY GNP KHÔNG ĐƯỢC LÀM RƠI bản kê khoảng ngày (duoc-CR-683 M4). Backend ghi đè cả
 * `metadata` mỗi lần lưu, nên khóa nào form không gửi lại là mất — sửa một chữ ở lý do là giấy
 * của đơn nhiều khoảng quay về chỉ còn bao ngoài.
 */
describe('GNP metadata round trip', () => {
  const leavePeriods = [
    { from_date: '2026-10-27', from_session: 'full', to_date: '2026-10-27', to_session: 'full', days: 1 },
    { from_date: '2026-11-03', from_session: 'afternoon', to_date: '2026-11-07', to_session: 'full', days: 4.5 },
  ]
  const metadata = {
    employee_id: 7,
    leave_type: 'annual',
    from_date: '2026-10-27',
    from_session: 'full',
    to_date: '2026-11-07',
    to_session: 'full',
    total_days: 5.5,
    reason: 'Việc nhà',
    handover_employee_id: 0,
    contact_phone: '',
    leave_periods: leavePeriods,
    leave_lines: [{ code: 'annual', name: 'Phép năm', days: 5.5 }],
  }
  //  Chỉ khối `metadata` là thứ bài này kiểm — các cột khác của văn bản không liên quan.
  const record = { metadata } as unknown as DocumentRecord

  it('editing a field and saving sends back leave_periods and leave_lines untouched', () => {
    const form = documentToForm(record)
    const leave = form.leave
    if (!leave) throw new Error('khối nghỉ phép phải có')
    const payload = formToPayload({ ...form, leave: { ...leave, reason: 'Đổi lý do' } }, true)
    expect(payload.metadata).toEqual({ ...metadata, reason: 'Đổi lý do' })
  })

  it('does not nest the kept keys under an `extra` key', () => {
    const payload = formToPayload(documentToForm(record), true)
    expect(payload.metadata && 'extra' in payload.metadata).toBe(false)
  })

  it('the ten form fields win over a stale copy of the same key', () => {
    const form = documentToForm(record)
    const leave = form.leave
    if (!leave) throw new Error('khối nghỉ phép phải có')
    const payload = formToPayload(
      { ...form, leave: { ...leave, extra: { ...leave.extra, reason: 'cũ' } } },
      true,
    )
    expect(payload.metadata?.reason).toBe('Việc nhà')
  })

  it('a non-leave document still sends no metadata', () => {
    expect(formToPayload(documentToForm(record), false).metadata).toBeUndefined()
  })
})
