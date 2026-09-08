import { describe, expect, it } from 'vitest'

import type { ChatReply, UpdateProposal } from '../types/assistant'
import type { DraftOffer } from './reply-offers'
import { draftNavigation, pickDraftOffer, pickFileOffer, pickUpdateOffer } from './reply-offers'

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

  it('tool soạn nháp YCTT trả target payment kèm danh sách khoản nợ đã chuẩn hóa', () => {
    const offer = pickDraftOffer(
      reply([
        {
          name: 'draft_payment_request',
          args: { supplier: 'NCCA' },
          rows: 2,
          draft: { kind: 'payment_request', payable_ids: [3, 5] },
        },
      ]),
    )
    expect(offer?.target).toBe('payment')
    expect(offer?.args).toEqual({ kind: 'payment_request', payable_ids: [3, 5] })
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

  it('CR-218: tool ticket_create trả target ticket kèm bản nháp phiếu hỗ trợ', () => {
    const offer = pickDraftOffer(
      reply([
        {
          name: 'ticket_create',
          args: { subject: 'Lỗi tải báo cáo' },
          rows: 1,
          draft: { kind: 'ticket', subject: 'Lỗi tải báo cáo', priority: 'normal' },
        },
      ]),
    )
    expect(offer?.target).toBe('ticket')
    expect(offer?.args).toEqual({ kind: 'ticket', subject: 'Lỗi tải báo cáo', priority: 'normal' })
  })
})

describe('pickUpdateOffer', () => {
  const proposal: UpdateProposal = {
    kind: 'update_proposal',
    entity: 'purchase_request',
    entity_label: 'Yêu cầu mua hàng',
    code: 'YCMH010126-001',
    doc_status_label: 'Nháp',
    changes: [{ field: 'purpose', label: 'Mục đích mua hàng', old: 'cũ', new: 'mới' }],
    confirm_token: 'tk',
    url: '/procurement/purchase-requests/5',
  }

  it('tool đề xuất sửa có khối proposal thì trả offer kèm token xác nhận', () => {
    const offer = pickUpdateOffer(
      reply([{ name: 'propose_document_update', args: {}, rows: 1, proposal }]),
    )
    expect(offer).toEqual({ conversationId: 7, proposal })
  })

  it('tool bị chặn quyền / lỗi (không có proposal) thì KHÔNG dựng thẻ xác nhận', () => {
    expect(
      pickUpdateOffer(reply([{ name: 'propose_document_update', args: {}, rows: 0 }])),
    ).toBeNull()
  })

  it('lượt không đề xuất gì thì trả null để gỡ thẻ của lượt trước', () => {
    //  Thẻ cũ hiện dai sẽ gây bấm nhầm — token vẫn hết hạn ở backend nhưng đừng thử người dùng.
    expect(pickUpdateOffer(reply([{ name: 'my_approval_tasks', args: {}, rows: 3 }]))).toBeNull()
    expect(pickUpdateOffer(reply(undefined))).toBeNull()
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

  it('tool xuất Excel cũng dựng được nút tải — lỗi từng gặp: bộ lọc cứng theo tên tool docx', () => {
    const offer = pickFileOffer(
      reply([
        {
          name: 'export_excel_file',
          args: {},
          file: { id: 2, filename: 'tien-do.xlsx', size: 10, download_url: '/api/f/2' },
        },
      ]),
    )
    expect(offer).toEqual({
      conversationId: 7,
      filename: 'tien-do.xlsx',
      downloadUrl: '/api/f/2',
    })
  })

  it('không có file thì trả null', () => {
    expect(pickFileOffer(reply([{ name: 'export_report_file', args: {} }]))).toBeNull()
  })
})

describe('draftNavigation — payment', () => {
  function paymentDraft(args: Record<string, unknown>): DraftOffer {
    return { conversationId: 1, target: 'payment', args }
  }

  it('builds ?payables= from payable_ids without passing router state', () => {
    //  YCTT cố ý KHÔNG truyền state: form tự nạp lại khoản nợ dưới quyền người đăng
    //  nhập (CR-025) — truyền state là tin dữ liệu chat, vòng qua hàng rào phạm vi.
    const nav = draftNavigation(paymentDraft({ payable_ids: [3, 7] }))
    expect(nav.to).toBe('/finance/payment-requests/new?payables=3,7')
    expect(nav.state).toBeUndefined()
  })

  it('appends &offsets= when the tool proposed FIFO offsets (CR-264)', () => {
    const nav = draftNavigation(
      paymentDraft({ payable_ids: [3, 7], offsets: { 3: 300, 7: 500 } }),
    )
    expect(nav.to).toBe('/finance/payment-requests/new?payables=3,7&offsets=3:300,7:500')
  })

  it('drops invalid offset entries and omits the param when nothing valid remains', () => {
    const nav = draftNavigation(
      paymentDraft({ payable_ids: [3], offsets: { 0: 100, '-1': 50, 3: 'abc', 4: 0 } }),
    )
    expect(nav.to).toBe('/finance/payment-requests/new?payables=3')
  })

  it('ignores a non-object offsets value from a raw model draft', () => {
    //  args thô do model gõ có thể sai kiểu bất kỳ — không được nổ, chỉ bỏ qua.
    const nav = draftNavigation(paymentDraft({ payable_ids: [3], offsets: '3:300' }))
    expect(nav.to).toBe('/finance/payment-requests/new?payables=3')
  })
})
