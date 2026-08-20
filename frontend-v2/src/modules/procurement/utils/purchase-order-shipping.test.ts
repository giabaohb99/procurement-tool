import { describe, expect, it } from 'vitest'

import type { PurchaseOrderDelivery, PurchaseOrderItem } from '../types/purchase-order-detail'
import { summarizeShipping } from './purchase-order-shipping'

function delivery(patch: Partial<PurchaseOrderDelivery>): PurchaseOrderDelivery {
  return {
    delivery_no: 1,
    warehouse_code: '',
    carrier_code: '',
    carrier_name: '',
    ship_qty: 0,
    ship_unit: '',
    received_qty: 0,
    promised_date: '',
    expected_date: '',
    received_date: '',
    std_days: 0,
    invoice_no: '',
    invoice_date: '',
    shipping_unit_price: 0,
    shipping_amount: 0,
    qc_result: '',
    extra_request: '',
    progress_note: '',
    ...patch,
  }
}

function item(deliveries: PurchaseOrderDelivery[]): PurchaseOrderItem {
  return {
    product_code: 'SP-1',
    product_name: 'Sản phẩm 1',
    invoice_name: '',
    item_group: '',
    spec: '',
    fg_code: '',
    fg_name: '',
    invoice_no: '',
    invoice_date: '',
    document_delivery_date: '',
    supplier_ready: false,
    required_date: '',
    expected_date: '',
    unit: 'Cái',
    qty_request: 0,
    qty_order: 0,
    price: 0,
    vat: 0,
    warehouse_code: '',
    note: '',
    deliveries,
  }
}

describe('summarizeShipping', () => {
  it('không có lần giao nào ghi cước thì mọi con số bằng 0', () => {
    expect(summarizeShipping([item([delivery({}), delivery({})])])).toEqual({
      total: 0,
      chargedCount: 0,
      missingCarrierCount: 0,
    })
  })

  /**
   * Đúng tình huống ĐMH 352 làm người dùng hỏi "7 triệu ở đâu ra": một chuyến xe
   * 3,5 triệu bị ghi lên CẢ HAI lần giao nên màn hình cộng thành 7 triệu. Đếm số
   * lần giao có cước là cách nhanh nhất để nhìn ra chuyện đó.
   */
  it('cộng cước của mọi lần giao và đếm số lần giao có cước', () => {
    const summary = summarizeShipping([
      item([delivery({ shipping_amount: 3_500_000, carrier_code: 'NCC-XE' })]),
      item([delivery({ shipping_amount: 3_500_000, carrier_code: 'NCC-XE' })]),
    ])

    expect(summary.total).toBe(7_000_000)
    expect(summary.chargedCount).toBe(2)
    expect(summary.missingCarrierCount).toBe(0)
  })

  it('đếm riêng lần giao có cước mà bỏ trống nhà xe — cước đó không thành công nợ', () => {
    const summary = summarizeShipping([
      item([
        delivery({ shipping_amount: 3_500_000 }),
        delivery({ shipping_amount: 3_500_000, carrier_code: 'NCC-XE' }),
      ]),
    ])

    expect(summary.missingCarrierCount).toBe(1)
    expect(summary.chargedCount).toBe(2)
  })

  it('bỏ qua lần giao cước bằng 0 hoặc âm, không tính là "có cước"', () => {
    const summary = summarizeShipping([
      item([delivery({ shipping_amount: 0 }), delivery({ shipping_amount: -100 })]),
    ])

    expect(summary).toEqual({ total: 0, chargedCount: 0, missingCarrierCount: 0 })
  })

  it('dòng hàng chưa có lần giao nào cũng không làm vỡ phép cộng', () => {
    const empty = item([])
    // Dòng mới thêm tay chưa chạm tới lần giao — `deliveries` có thể chưa tồn tại.
    delete (empty as { deliveries?: PurchaseOrderDelivery[] }).deliveries

    expect(summarizeShipping([empty]).total).toBe(0)
  })
})
