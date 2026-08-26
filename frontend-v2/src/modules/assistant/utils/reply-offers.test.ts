import { describe, expect, it } from 'vitest'

import type { ChatReply } from '../types/assistant'
import { pickDraftOffer, pickFileOffer } from './reply-offers'

function reply(toolCalls: ChatReply['tool_calls']): ChatReply {
  return {
    text: 'ok',
    provider: 'gemini',
    model: 'x',
    kind: 'general',
    usage: {
      input_tokens: 0,
      output_tokens: 0,
      thinking_tokens: 0,
      cache_read_tokens: 0,
      cache_write_tokens: 0,
    },
    conversation_id: 7,
    title: 't',
    tool_calls: toolCalls,
  }
}

describe('pickDraftOffer', () => {
  it('tool soạn nháp chạy thành công thì trả bản nháp kèm loại phiếu', () => {
    const offer = pickDraftOffer(
      reply([{ name: 'draft_purchase_request', args: { purpose: 'x' }, rows: 1 }]),
    )
    expect(offer).toEqual({ conversationId: 7, args: { purpose: 'x' }, target: 'purchase' })
  })

  it('ưu tiên bản draft đã chuẩn hóa từ kết quả tool thay vì args thô của model', () => {
    const offer = pickDraftOffer(
      reply([
        {
          name: 'draft_leave_request',
          args: { uom: 'cái' },
          rows: 1,
          draft: { uom: 'Cái' },
        },
      ]),
    )
    expect(offer?.args).toEqual({ uom: 'Cái' })
    expect(offer?.target).toBe('leave')
  })

  it('tool bị chặn quyền / lỗi (rows rỗng hoặc 0) thì KHÔNG chào nút', () => {
    //  Lỗi từng gặp: bot bảo "bấm nút bên dưới" trong khi tool trả denied — nút
    //  hiện ra sẽ mở form trống, người dùng tưởng mất dữ liệu.
    expect(pickDraftOffer(reply([{ name: 'draft_survey_request', args: {} }]))).toBeNull()
    expect(
      pickDraftOffer(reply([{ name: 'draft_survey_request', args: {}, rows: 0 }])),
    ).toBeNull()
  })

  it('lượt không gọi tool soạn nháp thì trả null để gỡ nút của lượt trước', () => {
    expect(pickDraftOffer(reply([{ name: 'my_approval_tasks', args: {}, rows: 3 }]))).toBeNull()
    expect(pickDraftOffer(reply(undefined))).toBeNull()
  })
})

describe('pickFileOffer', () => {
  it('tool xuất báo cáo có file thì trả tên + đường tải', () => {
    const offer = pickFileOffer(
      reply([
        {
          name: 'export_report_file',
          args: {},
          file: { id: 1, filename: 'bao-cao.docx', size: 10, download_url: '/api/f/1' },
        },
      ]),
    )
    expect(offer).toEqual({
      conversationId: 7,
      filename: 'bao-cao.docx',
      downloadUrl: '/api/f/1',
    })
  })

  it('không có file thì trả null', () => {
    expect(pickFileOffer(reply([{ name: 'export_report_file', args: {} }]))).toBeNull()
  })
})
