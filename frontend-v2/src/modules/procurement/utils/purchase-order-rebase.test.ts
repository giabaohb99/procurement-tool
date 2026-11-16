import { describe, expect, it } from 'vitest'

import type { PurchaseOrderDetail, PurchaseOrderItem } from '../types/purchase-order-detail'
import { createEmptyPurchaseOrder } from './purchase-order-draft'
import { rebasePurchaseOrderDraft } from './purchase-order-rebase'

function line(id: number | undefined, overrides: Partial<PurchaseOrderItem> = {}): PurchaseOrderItem {
  return {
    id,
    product_code: `VT${id ?? 'new'}`,
    product_name: 'Vật tư',
    invoice_name: '',
    item_group: '',
    spec: '',
    fg_code: '',
    fg_name: '',
    invoice_no: '',
    invoice_date: '',
    document_delivery_date: '',
    supplier_ready: true,
    required_date: '',
    expected_date: '',
    unit: 'Cái',
    qty_request: 10,
    qty_order: 10,
    price: 4250,
    vat: 8,
    warehouse_code: '',
    note: '',
    currency: '',
    exchange_rate: 0,
    weight_kg: 0,
    dimension: '',
    deliveries: [],
    progress_status: 'not_ordered',
    ...overrides,
  }
}

function order(items: PurchaseOrderItem[], overrides: Partial<PurchaseOrderDetail> = {}): PurchaseOrderDetail {
  return { ...createEmptyPurchaseOrder(), id: 1178, code: 'PO01178', items, ...overrides }
}

describe('rebasePurchaseOrderDraft (bao-CR-758)', () => {
  it('chưa sửa gì thì lấy nguyên bản máy chủ mới', () => {
    const base = order([line(1)])
    const server = order([line(1)], { document_status: 'complete' })
    expect(rebasePurchaseOrderDraft(base, base, server)).toBe(server)
  })

  it('giá vừa gõ (chưa lưu) giữ nguyên, phần máy chủ đổi vẫn cập nhật', () => {
    const base = order([line(1), line(2, { price: 1350 })])
    const draft = { ...base, items: [{ ...base.items[0], price: 5000 }, base.items[1]] }
    const server = order(
      [line(1, { progress_status: 'ordered' }), line(2, { price: 1350, note: 'máy chủ' })],
      { document_status: 'complete' },
    )

    const next = rebasePurchaseOrderDraft(base, draft, server)
    expect(next.items.map((item) => item.price)).toEqual([5000, 1350])
    expect(next.items[0].progress_status).toBe('ordered')
    expect(next.items[1].note).toBe('máy chủ')
    expect(next.document_status).toBe('complete')
  })

  it('ô đầu đơn người dùng đã sửa giữ nguyên', () => {
    const base = order([line(1)])
    const draft = { ...base, approver_employee_id: 77, inspection_days: 5 }
    const server = order([line(1)], { document_status: 'complete' })
    const next = rebasePurchaseOrderDraft(base, draft, server)
    expect(next.approver_employee_id).toBe(77)
    expect(next.inspection_days).toBe(5)
    expect(next.document_status).toBe('complete')
  })

  it('dòng mới chưa lưu giữ lại, dòng người dùng đã bỏ vẫn bỏ', () => {
    const base = order([line(1), line(2)])
    const draft = { ...base, items: [base.items[0], line(undefined, { price: 99 })] }
    const server = order([line(1), line(2)])
    const next = rebasePurchaseOrderDraft(base, draft, server)
    expect(next.items.map((item) => item.id)).toEqual([1, undefined])
    expect(next.items[1].price).toBe(99)
  })
})
