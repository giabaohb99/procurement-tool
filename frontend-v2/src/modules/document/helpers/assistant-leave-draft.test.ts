import { describe, expect, it } from 'vitest'

import { parseAssistantLeaveDraft } from './assistant-leave-draft'

const hopLe = {
  kind: 'leave_request',
  doc_type_id: 7,
  doc_type_code: 'GNP',
  title: 'Giấy nghỉ phép Người YC (01/09 - 03/09/2026)',
  leave: {
    leave_type: 'unpaid',
    from_date: '2026-09-01',
    from_session: 'full',
    to_date: '2026-09-03',
    to_session: 'afternoon',
    total_days: 2.5,
    reason: 'Về quê có việc gia đình',
    contact_phone: '0900000001',
  },
}

describe('parseAssistantLeaveDraft', () => {
  it('đọc đủ bản nháp hợp lệ, giữ nguyên số ngày và các ô đã chọn', () => {
    const draft = parseAssistantLeaveDraft(hopLe)
    expect(draft).not.toBeNull()
    expect(draft?.doc_type_id).toBe(7)
    expect(draft?.title).toContain('Giấy nghỉ phép')
    expect(draft?.leave.leave_type).toBe('unpaid')
    expect(draft?.leave.to_session).toBe('afternoon')
    expect(draft?.leave.total_days).toBe(2.5)
  })

  it('không nhận bản nháp thiếu kind — cùng ô state còn chở bản nháp YCBG/YCMH', () => {
    expect(parseAssistantLeaveDraft({ ...hopLe, kind: undefined })).toBeNull()
    expect(parseAssistantLeaveDraft({ purpose: 'Mua màn hình', lines: [] })).toBeNull()
  })

  it('thiếu phần cốt lõi (loại, ngày, lý do) thì trả null cho form mở trắng', () => {
    expect(parseAssistantLeaveDraft(null)).toBeNull()
    expect(parseAssistantLeaveDraft({ ...hopLe, doc_type_id: 0 })).toBeNull()
    expect(
      parseAssistantLeaveDraft({ ...hopLe, leave: { ...hopLe.leave, from_date: '' } }),
    ).toBeNull()
    expect(
      parseAssistantLeaveDraft({ ...hopLe, leave: { ...hopLe.leave, reason: '   ' } }),
    ).toBeNull()
  })

  it('giá trị lạ ở ô chọn về mặc định, số ngày rác về chuỗi rỗng cho ô gợi ý tự tính', () => {
    const draft = parseAssistantLeaveDraft({
      ...hopLe,
      leave: {
        ...hopLe.leave,
        leave_type: '',
        from_session: 'sáng',
        total_days: -1,
      },
    })
    expect(draft?.leave.leave_type).toBe('annual')
    expect(draft?.leave.from_session).toBe('full')
    expect(draft?.leave.total_days).toBe('')
  })
})
