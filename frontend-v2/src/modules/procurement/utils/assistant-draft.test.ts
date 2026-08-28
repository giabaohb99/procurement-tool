import { describe, expect, it } from 'vitest'

import { parseAssistantDraft, parsePurchaseAssistantDraft } from './assistant-draft'

describe('parseAssistantDraft', () => {
  it('đọc bản nháp đầy đủ: giữ mục đích, ghi chú và chuẩn hóa từng dòng', () => {
    const draft = parseAssistantDraft({
      purpose: '  Trang bị màn hình cho thiết kế  ',
      note: 'Ưu tiên giao trong tháng',
      lines: [
        {
          requirement_detail: 'Màn hình 27 inch, IPS, 2K',
          item_group: 'Thiết bị IT',
          request_qty: 2,
          uom: 'cái',
          proposed_price: 4500000,
          other_requirement: 'Bảo hành 24 tháng',
        },
      ],
    })
    expect(draft).not.toBeNull()
    expect(draft?.purpose).toBe('Trang bị màn hình cho thiết kế')
    expect(draft?.lines).toHaveLength(1)
    expect(draft?.lines[0].request_qty).toBe(2)
  })

  it('args do model điền nên phải phòng thủ: sai kiểu thì quy về rỗng/0, không vỡ trang', () => {
    const draft = parseAssistantDraft({
      purpose: 'Mua vật tư',
      lines: [
        // Dòng thiếu requirement_detail -> bị loại; số âm/chữ -> về 0.
        { item_group: 'X' },
        { requirement_detail: 'Găng tay bảo hộ', request_qty: 'nhiều', proposed_price: -5 },
      ],
    })
    expect(draft?.lines).toHaveLength(1)
    expect(draft?.lines[0].request_qty).toBe(0)
    expect(draft?.lines[0].proposed_price).toBe(0)
  })

  it('thiếu mục đích hoặc không còn dòng hợp lệ nào thì trả null để form mở trắng bình thường', () => {
    expect(parseAssistantDraft(null)).toBeNull()
    expect(parseAssistantDraft('xin chào')).toBeNull()
    expect(parseAssistantDraft({ purpose: '', lines: [{ requirement_detail: 'a' }] })).toBeNull()
    expect(parseAssistantDraft({ purpose: 'Mua', lines: [{}] })).toBeNull()
  })

  it('CR-218: dòng có ngày cần kết quả thì giữ, không có thì về rỗng chứ không undefined', () => {
    //  undefined lọt qua spread `{...EMPTY_LINE, ...line}` sẽ ĐÈ mất giá trị mặc định
    //  của form — phải luôn là chuỗi.
    const draft = parseAssistantDraft({
      purpose: 'Khảo sát giá',
      lines: [
        { requirement_detail: 'A', result_due_date: '2026-09-05' },
        { requirement_detail: 'B', result_due_date: 123 },
      ],
    })
    expect(draft?.lines[0].result_due_date).toBe('2026-09-05')
    expect(draft?.lines[1].result_due_date).toBe('')
  })
})

describe('parsePurchaseAssistantDraft', () => {
  it('CR-218: dòng có kho nhận thì giữ, sai kiểu thì về rỗng chứ không undefined', () => {
    const draft = parsePurchaseAssistantDraft({
      purpose: 'Mua vật tư',
      lines: [
        { product_name: 'Găng tay', warehouse: 'Kho Cần Thơ' },
        { product_name: 'Khẩu trang', warehouse: null },
      ],
    })
    expect(draft?.lines[0].warehouse).toBe('Kho Cần Thơ')
    expect(draft?.lines[1].warehouse).toBe('')
  })
})
