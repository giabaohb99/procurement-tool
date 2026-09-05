import { describe, expect, it } from 'vitest'

import type { PurchaseOrderDetail, PurchaseOrderItem } from '../types/purchase-order-detail'
import type {
  PurchaseRequestDetail,
  PurchaseRequestItem,
} from '../types/purchase-request-detail'
import type { SurveyRequestDetail, SurveyRequestLine } from '../types/survey-request-detail'
import {
  missingPurchaseOrderLineFields,
  missingPurchaseRequestLineFields,
  missingSurveyRequestLineFields,
  PURCHASE_ORDER_LINE_REQUIRED,
  validatePurchaseOrder,
  validatePurchaseRequest,
  validateSurveyRequest,
} from './required-fields'

/* ------------------------------------------------------------- khuôn mẫu -- */

/** Dòng YCMH ĐỦ ô bắt buộc; test chỉ ghi đè đúng ô nó muốn làm hỏng. */
function prLine(overrides: Partial<PurchaseRequestItem> = {}): PurchaseRequestItem {
  return {
    product_code: 'SP001',
    product_name: 'Bao bì carton 3 lớp',
    item_group: 'Bao bì',
    group_desc: '',
    qty: 100,
    unit: 'Cái',
    price: 12000,
    vat_pct: 8,
    amount: 0,
    warehouse: 'KHO-HN',
    required_date: '2026-09-01',
    assignee: '',
    expected_date: '',
    line_status: 'no_po',
    progress_note: '',
    note: '',
    qty_ordered: 0,
    qty_received: 0,
    product_id: 1,
    product_thumbnail_url: '',
    ...overrides,
  }
}

function prDoc(items: PurchaseRequestItem[]): PurchaseRequestDetail {
  return {
    id: 1,
    code: 'YCMH-001',
    company_id: 1,
    company_name: 'DEGO',
    requester: 'Nguyễn Văn A',
    requester_id: 5,
    requester_position: '',
    department: 'Sản xuất',
    head_of_dept: '',
    head_of_dept_id: 0,
    purpose: 'Đóng gói lô hàng tháng 9',
    request_date: '2026-08-20',
    need_date: '',
    status: 'draft',
    is_urgent: false,
    vat_rate: 0.08,
    assignee_id: 0,
    note: '',
    show_code_on_print: true,
    supplier_req: { name: '', tax_code: '', contact: '' },
    supplier_pur: { name: '', tax_code: '', contact: '' },
    supplier_from_survey: false,
    can_edit_supplier_pur: false,
    suggested_supplier: '',
    suggested_supplier_tax_code: '',
    suggested_supplier_contact: '',
    quote_filename: '',
    quote_file_url: '',
    dispatch_enabled: false,
    can_dispatch: false,
    can_approve: false,
    created_at: '',
    created_by_name: '',
    requester_signature: '',
    approver_name: '',
    approver_signature: '',
    dispatcher_name: '',
    dispatcher_signature: '',
    items,
    subtotal: 0,
    vat: 0,
    total: 0,
  }
}

function srLine(overrides: Partial<SurveyRequestLine> = {}): SurveyRequestLine {
  return {
    item_group: 'Bao bì',
    requirement_detail: 'Carton 3 lớp, in 2 màu',
    other_requirement: '',
    request_qty: 100,
    uom: 'Cái',
    proposed_price: 0,
    product_code: '',
    // bao-CR-289: bộ trường mirror YCMH — mặc định ĐỦ để dòng chuẩn qua cổng gửi duyệt.
    warehouse: 'Kho A',
    required_date: '2026-09-01',
    vat_pct: 8,
    qty_ordered: 0,
    qty_received: 0,
    expected_date: '',
    progress_note: '',
    purchaser_note: '',
    received_date: '',
    result_due_date: '',
    result_date: '',
    assignee: '',
    assignee_name: '',
    pr_id: 0,
    pr_code: '',
    po_id: 0,
    po_code: '',
    is_completed: false,
    line_status: '',
    no_option: false,
    option_count: 0,
    has_chosen: false,
    progress_state: '',
    progress_tone: '',
    ...overrides,
  }
}

function srDoc(lines: SurveyRequestLine[]): SurveyRequestDetail {
  return {
    id: 1,
    code: 'YCBG-001',
    company_id: 1,
    requester: 'Nguyễn Văn A',
    requester_id: 5,
    requester_position: '',
    department_id: 2,
    department: 'Sản xuất',
    head_of_dept_id: 0,
    head_of_dept: '',
    purpose: 'Tìm nhà cung cấp bao bì mới',
    request_date: '2026-08-20',
    status: 'draft',
    note: '',
    reject_reason: '',
    is_urgent: false,
    suggested_supplier: '',
    suggested_supplier_tax_code: '',
    suggested_supplier_contact: '',
    created_at: '',
    created_by: 0,
    merged_flow_enabled: true,
    lines,
  }
}

/** Dòng ĐMH ĐỦ 11 ô của cổng CR-095. */
function poLine(overrides: Partial<PurchaseOrderItem> = {}): PurchaseOrderItem {
  return {
    product_code: 'SP001',
    product_name: 'Bao bì carton 3 lớp',
    invoice_name: 'Thùng carton 3 lớp',
    item_group: 'Bao bì',
    spec: '',
    fg_code: '',
    fg_name: '',
    invoice_no: '',
    invoice_date: '',
    document_delivery_date: '',
    supplier_ready: true,
    required_date: '2026-09-01',
    expected_date: '2026-08-28',
    unit: 'Cái',
    qty_request: 100,
    qty_order: 100,
    price: 12000,
    vat: 8,
    warehouse_code: 'KHO-HN',
    note: '',
    deliveries: [],
    ...overrides,
  }
}

function poDoc(items: PurchaseOrderItem[]): PurchaseOrderDetail {
  return {
    id: 1,
    code: 'DMH-001',
    misa_code: '',
    pr_code: '',
    survey_code: '',
    company_id: 1,
    supplier_code: 'NCC001',
    supplier_name: 'Công ty Bao bì X',
    department: '',
    nspt: '',
    order_date: '2026-08-20',
    vat_rate: 0.08,
    payment_terms: '',
    is_urgent: false,
    status: 'draft',
    document_status: '',
    note: '',
    items,
    subtotal: 0,
    vat: 0,
    total: 0,
    shipping_total: 0,
    order_subtotal: 0,
    order_total: 0,
    unpaid_total: 0,
  }
}

/* ------------------------------------------------------------------ YCMH -- */

describe('validatePurchaseRequest', () => {
  it('cho LƯU phiếu nháp còn thiếu ô của dòng — chặn ngay từ nút Lưu là không ghi tạm được', () => {
    const data = prDoc([prLine({ warehouse: '', required_date: '' })])
    expect(validatePurchaseRequest(data)).toBe('')
  })

  it('chặn GỬI DUYỆT khi dòng thiếu ô, và gọi đích danh sản phẩm lẫn tên ô', () => {
    const data = prDoc([prLine({ warehouse: '', required_date: '' })])
    expect(validatePurchaseRequest(data, true)).toBe(
      'Sản phẩm "Bao bì carton 3 lớp" còn thiếu: Kho nhận, Ngày cần hàng.',
    )
  })

  it('số lượng 0 tính là chưa nhập', () => {
    expect(validatePurchaseRequest(prDoc([prLine({ qty: 0 })]), true)).toContain('Số lượng mua')
  })

  it('bỏ qua dòng chưa có tên sản phẩm — đó là dòng người lập thêm ra rồi để trống', () => {
    const data = prDoc([prLine(), prLine({ product_name: '', product_code: '', qty: 0 })])
    expect(validatePurchaseRequest(data, true)).toBe('')
  })

  it('chặn trùng mã hàng NGAY TỪ LÚC LƯU — dòng YCMH nối sang ĐMH bằng mã', () => {
    const data = prDoc([prLine(), prLine({ product_name: 'Dòng hai' })])
    expect(validatePurchaseRequest(data)).toContain('Mã hàng bị trùng: SP001')
  })

  it('thiếu công ty / nhân sự yêu cầu thì chặn cả khi Lưu vì backend không dựng nổi phiếu', () => {
    expect(validatePurchaseRequest({ ...prDoc([prLine()]), company_id: 0 })).toBe(
      'Vui lòng chọn Công ty',
    )
    expect(validatePurchaseRequest({ ...prDoc([prLine()]), requester: '' })).toBe(
      'Vui lòng chọn Nhân sự yêu cầu',
    )
  })

  it('phiếu đủ ô thì không báo gì', () => {
    expect(validatePurchaseRequest(prDoc([prLine()]), true)).toBe('')
  })
})

describe('missingPurchaseRequestLineFields', () => {
  it('liệt kê đúng bốn ô bắt buộc khi dòng trống trơn', () => {
    const empty = prLine({ product_code: '', qty: 0, warehouse: '', required_date: '' })
    expect(missingPurchaseRequestLineFields(empty)).toEqual([
      'Mã hàng',
      'Số lượng mua',
      'Kho nhận',
      'Ngày cần hàng',
    ])
  })

  it('ô chỉ có dấu cách vẫn là ô trống', () => {
    expect(missingPurchaseRequestLineFields(prLine({ warehouse: '   ' }))).toEqual(['Kho nhận'])
  })
})

/* ------------------------------------------------------------------ YCBG -- */

describe('validateSurveyRequest', () => {
  it('bắt buộc CỨNG ô Phân loại ở mỗi dòng — khách chốt bỏ luật "Phân loại HOẶC Chi tiết thông số"', () => {
    // Có mô tả thông số rất chi tiết vẫn không thay được Phân loại: phân loại là
    // thứ quyết định thời gian chuẩn để tính ngày trả kết quả.
    const data = srDoc([srLine({ item_group: '', requirement_detail: 'Mô tả rất dài và rõ' })])
    expect(validateSurveyRequest(data, true)).toBe('Dòng 1 còn thiếu: Phân loại.')
  })

  it('nêu đúng SỐ THỨ TỰ dòng bị thiếu, không phải dòng đầu tiên', () => {
    const data = srDoc([srLine(), srLine(), srLine({ item_group: '' })])
    expect(validateSurveyRequest(data, true)).toBe('Dòng 3 còn thiếu: Phân loại.')
  })

  it('lúc LƯU thì dòng thiếu Phân loại vẫn cất được', () => {
    expect(validateSurveyRequest(srDoc([srLine({ item_group: '' })]))).toBe('')
  })

  it('thiếu mục đích mua hàng thì chặn ngay từ lúc Lưu', () => {
    // bao-CR-289: phiếu gộp là Yêu cầu mua hàng nên câu chặn đổi theo nhãn mới.
    expect(validateSurveyRequest({ ...srDoc([srLine()]), purpose: '  ' })).toBe(
      'Vui lòng nhập Mục đích mua hàng',
    )
  })

  it('bao-CR-289: gửi duyệt bắt thêm Số lượng + Kho nhận + Ngày cần hàng như YCMH cũ', () => {
    const data = srDoc([srLine({ request_qty: 0, warehouse: '', required_date: '' })])
    expect(validateSurveyRequest(data, true)).toBe(
      'Dòng 1 còn thiếu: Số lượng dự kiến mua, Kho nhận, Ngày cần hàng.',
    )
    // Lúc LƯU vẫn cất được — luật chặn chỉ áp ở Gửi duyệt.
    expect(validateSurveyRequest(data)).toBe('')
  })

  it('bao-CR-289: Mã hàng CỐ Ý không bắt buộc — backend điền lúc chốt phương án', () => {
    expect(validateSurveyRequest(srDoc([srLine({ product_code: '' })]), true)).toBe('')
  })

  it('phiếu không có dòng nào thì chặn', () => {
    expect(validateSurveyRequest(srDoc([]))).toBe('Cần ít nhất 1 dòng sản phẩm cần khảo sát')
  })

  it('phiếu đủ ô thì không báo gì', () => {
    expect(validateSurveyRequest(srDoc([srLine()]), true)).toBe('')
  })
})

describe('missingSurveyRequestLineFields', () => {
  it('dòng có Phân loại thì không thiếu gì', () => {
    expect(missingSurveyRequestLineFields(srLine())).toEqual([])
  })
})

/* ------------------------------------------------------------------- ĐMH -- */

describe('validatePurchaseOrder', () => {
  it('cho LƯU đơn nháp còn thiếu ô của dòng', () => {
    expect(validatePurchaseOrder(poDoc([poLine({ unit: '', warehouse_code: '' })]))).toBe('')
  })

  it('gộp MỌI dòng thiếu vào một câu, giống hệt `submit_po` của backend', () => {
    // Báo lần lượt từng dòng thì người lập sửa xong dòng 1 lại bị chặn ở dòng 2,
    // tưởng màn hình hỏng.
    const data = poDoc([
      poLine({ product_code: 'SP001', unit: '' }),
      poLine({ product_code: 'SP002', expected_date: '', price: 0 }),
    ])
    expect(validatePurchaseOrder(data, true)).toBe(
      'Chưa gửi duyệt được — còn thiếu dòng 1 (SP001): ĐVT; ' +
        'dòng 2 (SP002): Ngày dự kiến có hàng, Đơn giá.',
    )
  })

  it('dòng chưa có mã hàng thì gọi thẳng là "chưa có mã hàng" thay vì để ngoặc rỗng', () => {
    const data = poDoc([poLine({ product_code: '' })])
    expect(validatePurchaseOrder(data, true)).toContain('dòng 1 (chưa có mã hàng): Mã hàng')
  })

  it('KHÔNG bắt buộc VAT — 0 vừa nghĩa chưa nhập vừa nghĩa hàng 0%, chặn là chặn oan', () => {
    expect(PURCHASE_ORDER_LINE_REQUIRED.map((field) => field.label)).not.toContain('VAT')
    expect(validatePurchaseOrder(poDoc([poLine({ vat: 0 })]), true)).toBe('')
  })

  it('chặn trùng mã hàng ngay từ lúc Lưu', () => {
    const data = poDoc([poLine(), poLine()])
    expect(validatePurchaseOrder(data)).toContain('Mã hàng bị trùng: SP001')
  })

  it('thiếu công ty / nhà cung cấp thì chặn cả khi Lưu', () => {
    expect(validatePurchaseOrder({ ...poDoc([poLine()]), company_id: 0 })).toBe(
      'Vui lòng chọn Công ty nhận hóa đơn',
    )
    expect(validatePurchaseOrder({ ...poDoc([poLine()]), supplier_code: '' })).toBe(
      'Vui lòng chọn Nhà cung cấp bán hàng',
    )
  })

  it('đơn đủ ô thì không báo gì', () => {
    expect(validatePurchaseOrder(poDoc([poLine()]), true)).toBe('')
  })
})

describe('missingPurchaseOrderLineFields', () => {
  it('giữ đúng 11 ô và đúng thứ tự của `TRUONG_BAT_BUOC_DONG` bên backend', () => {
    // Lệch danh sách này là màn cho bấm Gửi duyệt rồi API mới trả 400 — hoặc
    // ngược lại, màn chặn một ô mà backend không hề bắt.
    const empty = poLine({
      product_code: '',
      item_group: '',
      product_name: '',
      invoice_name: '',
      required_date: '',
      expected_date: '',
      unit: '',
      warehouse_code: '',
      qty_request: 0,
      qty_order: 0,
      price: 0,
    })
    expect(missingPurchaseOrderLineFields(empty)).toEqual([
      'Mã hàng',
      'Phân loại',
      'Tên hàng',
      'Tên trên hóa đơn',
      'Ngày yêu cầu có hàng',
      'Ngày dự kiến có hàng',
      'ĐVT',
      'Kho nhận mặc định',
      'SL yêu cầu',
      'SL đặt NCC',
      'Đơn giá',
    ])
  })

  it('SL yêu cầu và Ngày dự kiến có hàng nằm trong danh sách — hai ô v2 từng KHÔNG có chỗ nhập', () => {
    // Trước CR này `PurchaseOrderItem` còn thiếu hẳn `expected_date`, và popup
    // chi tiết dòng không có ô nào cho `qty_request`; người lập bị chặn mà không
    // biết sửa ở đâu.
    expect(missingPurchaseOrderLineFields(poLine({ qty_request: 0 }))).toEqual(['SL yêu cầu'])
    expect(missingPurchaseOrderLineFields(poLine({ expected_date: '' }))).toEqual([
      'Ngày dự kiến có hàng',
    ])
  })
})
