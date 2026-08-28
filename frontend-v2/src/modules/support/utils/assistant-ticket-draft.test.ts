import { describe, expect, it } from 'vitest'

import { parseAssistantTicketDraft } from './assistant-ticket-draft'

describe('parseAssistantTicketDraft', () => {
  it('đọc bản nháp đầy đủ: giữ chủ đề, bộ phận, ưu tiên và nội dung', () => {
    const draft = parseAssistantTicketDraft({
      kind: 'ticket',
      subject: '  Lỗi tải báo cáo thu mua  ',
      department: 'Hệ thống / CNTT',
      priority: 'high',
      body: 'Bấm Tải báo cáo thì trang trắng.',
    })
    expect(draft).toEqual({
      subject: 'Lỗi tải báo cáo thu mua',
      department: 'Hệ thống / CNTT',
      priority: 'high',
      body: 'Bấm Tải báo cáo thì trang trắng.',
    })
  })

  it('sai kind hoặc không phải object thì trả null — cùng khuôn state với các bản nháp khác', () => {
    expect(parseAssistantTicketDraft(null)).toBeNull()
    expect(parseAssistantTicketDraft('xin chào')).toBeNull()
    expect(
      parseAssistantTicketDraft({ kind: 'leave_request', subject: 'a', body: 'b' }),
    ).toBeNull()
  })

  it('thiếu chủ đề hoặc nội dung thì trả null để trang mở bình thường không dialog', () => {
    expect(parseAssistantTicketDraft({ kind: 'ticket', subject: '', body: 'b' })).toBeNull()
    expect(parseAssistantTicketDraft({ kind: 'ticket', subject: 'a', body: '   ' })).toBeNull()
  })

  it('ưu tiên lạ do model bịa thì quy về normal, bộ phận sai kiểu thì về rỗng', () => {
    const draft = parseAssistantTicketDraft({
      kind: 'ticket',
      subject: 'a',
      body: 'b',
      priority: 'sieu-khan',
      department: 12,
    })
    expect(draft?.priority).toBe('normal')
    expect(draft?.department).toBe('')
  })
})
