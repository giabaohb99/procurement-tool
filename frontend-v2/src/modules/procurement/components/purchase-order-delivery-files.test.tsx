import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { PurchaseOrderDeliveryFiles } from './purchase-order-delivery-files'

//  Chỉ soi chữ trên nút — cắt lượt gọi danh sách tệp của lần giao.
vi.mock('../hooks/use-purchase-request-support', () => ({
  usePurchaseRequestAttachments: () => ({ data: [] }),
  useUploadPurchaseRequestAttachments: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useDeletePurchaseRequestAttachment: () => ({ mutateAsync: vi.fn(), isPending: false }),
}))

/** duoc-CR-741 — chữ nút tệp của lần giao theo bản v1. */
describe('PurchaseOrderDeliveryFiles', () => {
  it('says Tải on a saved delivery (uploads right away)', () => {
    render(
      <PurchaseOrderDeliveryFiles
        deliveryId={12}
        purchaseOrderId={5}
        editable
        pendingFiles={[]}
        onPendingFilesChange={vi.fn()}
      />,
    )
    expect(screen.getByRole('button', { name: 'Tải' })).toHaveAttribute('type', 'button')
  })

  it('says Chọn tệp on an unsaved delivery (held until the order is saved)', () => {
    render(
      <PurchaseOrderDeliveryFiles
        purchaseOrderId={5}
        editable
        pendingFiles={[new File(['x'], 'phieu-giao.pdf')]}
        onPendingFilesChange={vi.fn()}
      />,
    )
    expect(screen.getByRole('button', { name: 'Chọn tệp' })).toBeInTheDocument()
    expect(screen.getByText('Tệp sẽ được tải lên khi bấm Lưu đơn.')).toBeInTheDocument()
  })

  it('shows no upload button to a read-only viewer', () => {
    render(
      <PurchaseOrderDeliveryFiles
        deliveryId={12}
        purchaseOrderId={5}
        editable={false}
        pendingFiles={[]}
        onPendingFilesChange={vi.fn()}
      />,
    )
    expect(screen.queryByRole('button', { name: 'Tải' })).toBeNull()
  })
})
