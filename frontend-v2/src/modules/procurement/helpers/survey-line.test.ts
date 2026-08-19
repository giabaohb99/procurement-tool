import { describe, expect, it } from 'vitest'

import {
  sectionsOf,
  type SurveyDetail,
  type SurveyLine,
  type SurveyTable,
} from '../types/survey-detail'
import {
  applyLineChange,
  calcAmount,
  isSupplierFromCatalog,
  lineHasContent,
  rowAmount,
  toPayloadLine,
  validateSurveySubmit,
} from './survey-line'

/** Dòng điền đủ mọi ô — nền để thử từng ô một bị bỏ trống. */
function filledLine(table: SurveyTable): SurveyLine {
  const line: SurveyLine = {}
  for (const section of sectionsOf(table)) {
    for (const field of section.fields) {
      if (field.type === 'check') line[field.key] = false
      else if (field.type === 'num' || field.type === 'vat' || field.type === 'computed') {
        line[field.key] = 1
      } else line[field.key] = 'x'
    }
  }
  return line
}

function header(changes: Partial<SurveyDetail> = {}): SurveyDetail {
  return {
    id: 1,
    code: 'KS-0001',
    survey_type: 'product',
    pr_code: '',
    survey_request_id: 0,
    sr_code: '',
    received_date: '2026-08-19',
    result_due_date: '',
    item_group: 'Bao bì',
    main_content: 'Khảo sát thùng carton',
    requirement_detail: 'Thùng 3 lớp, in 2 màu',
    request_qty: 0,
    nspt: 'Nguyễn Văn A',
    has_product_code: false,
    item_code: '',
    item_name: '',
    uom: '',
    proposed_rate: 0,
    approve_status: '',
    approve_note: '',
    status: 'draft',
    created_at: '2026-08-19T00:00:00',
    created_by: 1,
    supplier_lines: [],
    product_lines: [],
    supplier_count: 0,
    product_count: 0,
    subtotal: 0,
    main: '',
    ...changes,
  }
}

describe('thành tiền của dòng khảo sát', () => {
  it('nhân giá với MOQ rồi cộng VAT', () => {
    expect(calcAmount({ price_by_volume: 1000, moq: 10, vat: 10 })).toBe(11_000)
  })

  it('nhận cả số gõ từ form dưới dạng chuỗi', () => {
    expect(calcAmount({ price_by_volume: '1000', moq: '10', vat: '' })).toBe(10_000)
  })

  it('ưu tiên thành tiền đã lưu — báo giá trọn gói bị tính đè là mất số người dùng nhập', () => {
    expect(rowAmount({ price_by_volume: 1000, moq: 10, vat: 0, amount: 8000 })).toBe(8000)
  })

  it('tính lại khi đổi giá, nhưng để yên khi chính ô thành tiền đang được gõ đè', () => {
    const line: SurveyLine = { price_by_volume: 1000, moq: 10, vat: 0, amount: 10_000 }
    expect(applyLineChange(line, { price_by_volume: 2000 }).amount).toBe(20_000)
    expect(applyLineChange(line, { amount: 9500 }).amount).toBe(9500)
  })
})

describe('dòng có nội dung hay không', () => {
  it('dòng chỉ mang ô duyệt của TP/QL vẫn là dòng rỗng, không lưu xuống DB', () => {
    const line: SurveyLine = { line_approve: 'Chờ duyệt', line_approve_note: '' }
    expect(lineHasContent(line, 'supplier')).toBe(false)
  })

  it('chỉ cần một ô có chữ là dòng được lưu', () => {
    expect(lineHasContent({ supplier_code: 'NCC01' }, 'supplier')).toBe(true)
  })
})

describe('dữ liệu gửi lên backend', () => {
  it('bỏ ô "NCC sẵn có" — ô này chỉ đổi kiểu ô nhập, không có cột trong DB', () => {
    const payload = toPayloadLine({ supplier_code: 'NCC01', supplier_available: true }, 'supplier')
    expect(payload).not.toHaveProperty('supplier_available')
    expect(payload.supplier_code).toBe('NCC01')
  })

  it('bỏ luôn "Tên pháp lý" ở bảng SẢN PHẨM — bảng dòng SP không có cột đó (CR-091)', () => {
    const payload = toPayloadLine({ supplier_code: 'NCC01', supplier_name: 'Công ty X' }, 'product')
    expect(payload).not.toHaveProperty('supplier_name')
  })

  it('ép ô số về kiểu số và chốt lại thành tiền lúc gửi', () => {
    const payload = toPayloadLine(
      { product_name: 'Thùng', price_by_volume: '1000', moq: '10', vat: '10' },
      'product',
    )
    expect(payload.moq).toBe(10)
    expect(payload.amount).toBe(11_000)
  })
})

describe('ô NCC đang chọn từ danh mục hay gõ tay', () => {
  it('mã không có trong danh mục thì giữ ô gõ tay — bản v1 để mặc định "có sẵn" nên tải lại phiếu là mất tên NCC', () => {
    expect(isSupplierFromCatalog({ supplier_code: 'CHUA_CO' }, new Set(['NCC01']))).toBe(false)
  })

  it('danh mục chưa tải xong thì coi như có sẵn, tránh cả bảng nhấp nháy', () => {
    expect(isSupplierFromCatalog({ supplier_code: 'NCC01' }, new Set())).toBe(true)
  })
})

describe('kiểm tra trước khi gửi duyệt', () => {
  it('VAT 0% vẫn gửi được — hàng không chịu thuế mà bị chặn thì cả phiếu tắc', () => {
    const line = { ...filledLine('product'), vat: 0 }
    const result = validateSurveySubmit(header(), [], [line])
    expect(result.message).toBe('')
    expect(result.invalid.size).toBe(0)
  })

  it('chỉ ra đúng ô còn trống để tô đỏ', () => {
    const line = { ...filledLine('product'), origin: '' }
    const result = validateSurveySubmit(header(), [], [line])
    expect(result.invalid.has('product-0-origin')).toBe(true)
    expect(result.message).toContain('Dòng SP #1')
  })

  it('phiếu không có dòng nào thì báo ngay, khỏi để người dùng gửi phiếu rỗng', () => {
    expect(validateSurveySubmit(header(), [], []).message).toContain('ít nhất một dòng')
  })

  it('hàng đã có mã thì bắt khai đủ mã, số lượng, ĐVT và đơn giá đề xuất', () => {
    const result = validateSurveySubmit(header({ has_product_code: true }), [], [filledLine('product')])
    expect(result.message).toContain('Chưa chọn Mã hàng')
    expect(result.message).toContain('Số lượng yêu cầu')
  })
})
