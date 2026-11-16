import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { createEmptyPurchaseOrder } from '../utils/purchase-order-draft'
import { listPurchaseOrderLineIssues } from '../utils/required-fields'
import type { PurchaseOrderItem } from '../types/purchase-order-detail'
import { PurchaseOrderMissingFieldsNotice } from './purchase-order-missing-fields-notice'

function line(overrides: Partial<PurchaseOrderItem>): PurchaseOrderItem {
  return {
    product_code: 'VT01',
    product_name: 'Vật tư 01',
    invoice_name: 'Vật tư 01',
    item_group: 'Bao bì',
    spec: '',
    fg_code: '',
    fg_name: '',
    invoice_no: '',
    invoice_date: '',
    document_delivery_date: '',
    supplier_ready: true,
    required_date: '2026-11-20',
    expected_date: '2026-11-20',
    unit: 'Cái',
    qty_request: 10,
    qty_order: 10,
    price: 4250,
    vat: 8,
    warehouse_code: 'KHO-HN',
    note: '',
    currency: '',
    exchange_rate: 0,
    weight_kg: 0,
    dimension: '',
    deliveries: [],
    ...overrides,
  }
}

describe('PurchaseOrderMissingFieldsNotice (bao-CR-758)', () => {
  it('liệt kê theo dòng đúng ba ô v1 hay nhắc: Tên trên hóa đơn, Kho nhận mặc định, Đơn giá', () => {
    const order = {
      ...createEmptyPurchaseOrder(),
      items: [
        line({ product_code: 'VT01', invoice_name: '', warehouse_code: '', price: 0 }),
        line({ product_code: 'VT02' }),
        line({ product_code: 'VT03', warehouse_code: '' }),
      ],
    }
    render(<PurchaseOrderMissingFieldsNotice issues={listPurchaseOrderLineIssues(order)} />)

    expect(screen.getByText('Còn thiếu thông tin bắt buộc — chưa gửi duyệt được')).toBeInTheDocument()
    expect(
      screen.getByText('Dòng 1 (VT01): Tên trên hóa đơn, Kho nhận mặc định, Đơn giá'),
    ).toBeInTheDocument()
    expect(screen.queryByText(/Dòng 2/)).not.toBeInTheDocument()
    expect(screen.getByText('Dòng 3 (VT03): Kho nhận mặc định')).toBeInTheDocument()
  })

  it('đủ thông tin thì không dựng khung', () => {
    const order = { ...createEmptyPurchaseOrder(), items: [line({})] }
    const { container } = render(
      <PurchaseOrderMissingFieldsNotice issues={listPurchaseOrderLineIssues(order)} />,
    )
    expect(container).toBeEmptyDOMElement()
  })

  it('dòng trống chưa chọn hàng không bị đếm — khớp bộ lọc lúc lưu', () => {
    const order = {
      ...createEmptyPurchaseOrder(),
      items: [line({}), line({ product_code: '', product_name: '', price: 0 })],
    }
    expect(listPurchaseOrderLineIssues(order)).toEqual([])
  })
})
