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
  invalidRowIndexes,
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
    approve_status: 'pending',
    approve_status_label: 'Chưa xét duyệt',
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

describe('invalidRowIndexes', () => {
  it('gom khóa `bảng-dòng-ô` về đúng chỉ số dòng của bảng được hỏi', () => {
    const invalid = new Set(['supplier-0-contact_phone', 'supplier-2-note', 'product-1-origin'])

    expect([...invalidRowIndexes(invalid, 'supplier')].sort()).toEqual([0, 2])
    expect([...invalidRowIndexes(invalid, 'product')]).toEqual([1])
  })

  it('nhiều ô thiếu trên CÙNG một dòng vẫn chỉ ra một chỉ số', () => {
    //  Thẻ chỉ có một dấu cảnh báo cho cả dòng; đếm trùng ở đây thì không sai
    //  màn hình nhưng là dấu hiệu hàm đang gom nhầm mức.
    const invalid = new Set(['product-3-origin', 'product-3-moq', 'product-3-quote_unit'])
    expect([...invalidRowIndexes(invalid, 'product')]).toEqual([3])
  })

  it('KHÔNG lẫn bảng: tiền tố `product` không được khớp khi hỏi `supplier`', () => {
    const invalid = new Set(['product-0-origin'])
    expect(invalidRowIndexes(invalid, 'supplier').size).toBe(0)
  })

  it('tập rỗng trả về tập rỗng, không nổ', () => {
    expect(invalidRowIndexes(new Set(), 'supplier').size).toBe(0)
  })

  it('khóa méo bị BỎ QUA thay vì đẻ ra một chỉ số dòng có thật', () => {
    //  `Number('')` ra 0 và `Number('1e2')` ra 100 — hai ca này mà lọt thì thẻ
    //  số 1 (hoặc 101) bị gắn cờ "thiếu ô" trong khi nó đầy đủ, và người dùng
    //  đi tìm một chỗ trống không tồn tại.
    const invalid = new Set([
      'supplier--note', // thiếu hẳn số dòng
      'supplier-abc-note', // số dòng không phải số
      'supplier-1.5-note', // số lẻ
      'supplier-0', // thiếu tên ô
      'supplier', // trơ trọi
    ])
    expect(invalidRowIndexes(invalid, 'supplier').size).toBe(0)
  })

  it('ô có dấu GẠCH NGANG trong tên vẫn ra đúng dòng', () => {
    //  Cột hiện đều dùng gạch dưới, nhưng cắt bằng `split('-')[1]` thì một cột
    //  tên `giao-hang` sẽ làm hàm im lặng trả sai. Chốt lại hành vi đúng.
    const invalid = new Set(['supplier-4-giao-hang-tan-noi'])
    expect([...invalidRowIndexes(invalid, 'supplier')]).toEqual([4])
  })
})
