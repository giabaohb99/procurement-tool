import { describe, expect, it } from 'vitest'

import type { PurchaseOrderDetail } from '../types/purchase-order-detail'
import { buildPrepayPayable } from './build-prepay-payable'

function makeOrder(overrides: Partial<PurchaseOrderDetail> = {}): PurchaseOrderDetail {
  return {
    id: 10,
    code: 'PO25090001',
    misa_code: 'MISA-77',
    pr_code: '',
    survey_code: '',
    company_id: 3,
    supplier_code: 'NCC001',
    supplier_name: 'Công ty TNHH A',
    department: '',
    nspt: '',
    order_date: '2026-09-03',
    vat_rate: 8,
    payment_terms: '',
    is_urgent: false,
    status: 'approved',
    document_status: '',
    note: '',
    items: [],
    subtotal: 0,
    vat: 0,
    total: 0,
    shipping_total: 0,
    order_subtotal: 100_000,
    order_total: 108_000,
    unpaid_total: 0,
    ...overrides,
  }
}

describe('buildPrepayPayable', () => {
  it('lấy tiền theo SL ĐẶT, không lấy tiền theo SL thực nhận', () => {
    // Chưa nhận hàng nên `total` = 0; lấy nhầm cột này là phiếu trả trước 0 đồng.
    const row = buildPrepayPayable(makeOrder({ order_total: 108_000, total: 0 }))

    expect(row.total).toBe(108_000)
    expect(row.remaining).toBe(108_000)
    expect(row.paid_amount).toBe(0)
  })

  it('rơi về tiền thực nhận khi đơn không có tiền theo SL đặt', () => {
    expect(buildPrepayPayable(makeOrder({ order_total: 0, total: 55_000 })).total).toBe(55_000)
  })

  it('đơn không có tiền ở cả hai cột thì trả 0 chứ không trả NaN', () => {
    const row = buildPrepayPayable(
      // Backend có thể trả `null` cho cột tiền của đơn vừa tạo.
      makeOrder({ order_total: null as unknown as number, total: undefined as unknown as number }),
    )

    expect(row.total).toBe(0)
    expect(row.remaining).toBe(0)
  })

  // `payable_id = 0` là dấu hiệu "dòng gõ tay" của màn tạo YCTT. Đặt id thật vào
  // đây là phiếu đi trừ vào một khoản nợ KHÔNG tồn tại.
  it('luôn để id = 0 để phiếu không trừ vào khoản nợ nào', () => {
    expect(buildPrepayPayable(makeOrder()).id).toBe(0)
  })

  it('mượn mã MISA làm số chứng từ, đơn chưa có mã thì để trống', () => {
    expect(buildPrepayPayable(makeOrder({ misa_code: 'MISA-77' })).invoice_no).toBe('MISA-77')
    expect(buildPrepayPayable(makeOrder({ misa_code: '' })).invoice_no).toBe('')
  })

  it('giữ nguyên nhà cung cấp và công ty của đơn để phiếu về đúng pháp nhân', () => {
    const row = buildPrepayPayable(makeOrder({ supplier_code: 'NCC009', company_id: 7 }))

    expect(row.supplier_code).toBe('NCC009')
    expect(row.company_id).toBe(7)
    expect(row.source_type).toBe('goods')
  })

  it('không bịa ngày phát sinh hay hạn trả — chưa nhận hàng thì chưa có ngày nào', () => {
    const row = buildPrepayPayable(makeOrder())

    expect(row.incur_date).toBe('')
    expect(row.due_date).toBe('')
  })
})
