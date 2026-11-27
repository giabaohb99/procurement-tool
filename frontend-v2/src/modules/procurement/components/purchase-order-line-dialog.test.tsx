import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type { PurchaseOrderItem } from '../types/purchase-order-detail'
import { PurchaseOrderLineDialog } from './purchase-order-line-dialog'

//  Hộp chi tiết dòng chỉ soi cụm nút tiến độ — cắt các lượt gọi danh mục.
vi.mock('../hooks/use-purchase-request-support', () => ({
  usePurchaseRequestUnits: () => ({ data: { items: [] } }),
  usePurchaseRequestItemGroups: () => ({ data: { items: [] } }),
  usePurchaseRequestWarehouses: () => ({ data: { items: [] } }),
  usePurchaseRequestAttachments: () => ({ data: [] }),
  useUploadPurchaseRequestAttachments: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useDeletePurchaseRequestAttachment: () => ({ mutateAsync: vi.fn(), isPending: false }),
}))

function line(overrides: Partial<PurchaseOrderItem> = {}): PurchaseOrderItem {
  return {
    id: 501,
    product_code: 'ABA36',
    product_name: 'Abamectin 3.6EC',
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
    unit: 'Lít',
    qty_request: 0,
    qty_order: 10,
    price: 1000,
    vat: 0,
    warehouse_code: '',
    note: '',
    currency: '',
    exchange_rate: 0,
    weight_kg: 0,
    dimension: '',
    deliveries: [],
    progress_status: 'ordered',
    ...overrides,
  }
}

function renderDialog(props: Partial<Parameters<typeof PurchaseOrderLineDialog>[0]> = {}) {
  return render(
    <PurchaseOrderLineDialog
      item={line()}
      order={{ order_type: 1, currency: 'VND', exchange_rate: 1 }}
      lineNumber={1}
      open
      editable={false}
      afterApproveEditable={false}
      deliveryEditable
      attachEditable
      purchaseOrderId={5}
      carriers={[]}
      orderDate="2026-11-01"
      pendingFiles={{}}
      onChange={vi.fn()}
      onPendingFilesChange={vi.fn()}
      onDeliveryRemoved={vi.fn()}
      onOpenChange={vi.fn()}
      onSave={vi.fn()}
      {...props}
    />,
  )
}

/** duoc-CR-741 — popup chi tiết dòng có nút Tạm ngưng / Tiếp tục / Hủy như bản v1. */
describe('PurchaseOrderLineDialog — tiến độ dòng', () => {
  it('pauses or cancels the line through the same callback as the table', async () => {
    const onProgressChange = vi.fn()
    renderDialog({ progressEditable: true, onProgressChange })
    await userEvent.click(screen.getByRole('button', { name: 'Tạm ngưng' }))
    expect(onProgressChange).toHaveBeenCalledWith(expect.objectContaining({ id: 501 }), 'paused')
  })

  it('hides the buttons on an unsaved line, a locked line, or without permission', () => {
    const { unmount } = renderDialog({ progressEditable: true, item: line({ id: undefined }) })
    expect(screen.queryByRole('button', { name: 'Tạm ngưng' })).toBeNull()
    unmount()

    const second = renderDialog({ progressEditable: true, item: line({ progress_status: 'completed' }) })
    expect(screen.queryByRole('button', { name: 'Tạm ngưng' })).toBeNull()
    second.unmount()

    renderDialog({ progressEditable: false })
    expect(screen.queryByRole('button', { name: 'Tạm ngưng' })).toBeNull()
  })
})

/** duoc-CR-776 — hộp chi tiết dòng cho gõ cả đơn giá trước thuế lẫn sau VAT. */
describe('PurchaseOrderLineDialog — nhập giá sau VAT', () => {
  it('back-computes the pre-VAT price from the typed post-VAT price', async () => {
    const onChange = vi.fn()
    renderDialog({ editable: true, item: line({ price: 0, vat: 8 }), onChange })

    await userEvent.type(screen.getByLabelText(/^Đơn giá \(Sau VAT\)/), '108000')
    expect(onChange).toHaveBeenLastCalledWith(
      expect.objectContaining({ price: 100000, price_after_vat_input: 108000 }),
    )
  })

  it('typing the pre-VAT price drops any typed post-VAT value', async () => {
    const onChange = vi.fn()
    renderDialog({
      editable: true,
      item: line({ price: 92592.5926, vat: 8, price_after_vat_input: 100000 }),
      onChange,
    })

    expect(screen.getByLabelText(/^Đơn giá \(Sau VAT\)/)).toHaveValue('100.000')
    const pre = screen.getByLabelText(/^Đơn giá(?! \()/)
    await userEvent.clear(pre)
    await userEvent.type(pre, '5')
    expect(onChange).toHaveBeenLastCalledWith(
      expect.objectContaining({ price: 5, price_after_vat_input: undefined }),
    )
  })

  it('shows both prices read-only on a locked order, and drops post-VAT on import orders', () => {
    const { unmount } = renderDialog({ item: line({ price: 100000, vat: 8 }) })
    expect(screen.queryByLabelText(/^Đơn giá \(Sau VAT\)/)).toBeNull()
    expect(screen.getByText('108.000 đ')).toBeInTheDocument()
    unmount()

    renderDialog({ editable: true, order: { order_type: 2, currency: 'USD', exchange_rate: 25_000 } })
    expect(screen.queryByText(/^Đơn giá \(Sau VAT\)/)).toBeNull()
  })
})

describe('PurchaseOrderLineDialog — sửa giá sau duyệt', () => {
  it('drops the old "bấm Hủy duyệt" banner on an approved order', () => {
    renderDialog({ afterApproveEditable: true })
    expect(screen.queryByText(/Hủy duyệt/)).not.toBeInTheDocument()
  })

  it('offers a Sửa giá button next to the quantity line and starts reprice mode without closing', async () => {
    const onStartReprice = vi.fn()
    const onOpenChange = vi.fn()
    renderDialog({ afterApproveEditable: true, onStartReprice, onOpenChange })
    await userEvent.click(screen.getByRole('button', { name: 'Sửa giá' }))
    expect(onStartReprice).toHaveBeenCalledTimes(1)
    expect(onOpenChange).not.toHaveBeenCalled()
  })

  it('hides the Sửa giá button once reprice mode is on and swaps Lưu đơn for Xong', () => {
    renderDialog({ onStartReprice: vi.fn(), reprice: { original: line(), lockReason: '' } })
    expect(screen.queryByRole('button', { name: 'Sửa giá' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Xong' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Lưu đơn' })).not.toBeInTheDocument()
  })
})
