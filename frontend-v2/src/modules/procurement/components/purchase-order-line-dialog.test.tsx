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
