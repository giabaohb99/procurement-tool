import { fireEvent, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { PurchaseOrderDeliveryAttachDialog } from './purchase-order-delivery-attach-dialog'

const upload = vi.fn()
const uploadArgs: unknown[][] = []

vi.mock('../hooks/use-purchase-request-support', () => ({
  useUploadPurchaseRequestAttachments: (...args: unknown[]) => {
    uploadArgs.push(args)
    return { mutateAsync: upload, isPending: false }
  },
  usePurchaseRequestAttachments: () => ({
    data: [{ id: 5, filename: 'hd-6265.pdf', url: '/f/5', content_type: 'application/pdf' }],
  }),
  useDeletePurchaseRequestAttachment: () => ({ mutateAsync: vi.fn(), isPending: false }),
}))

function renderDialog(onOpenChange = vi.fn()) {
  render(
    <PurchaseOrderDeliveryAttachDialog
      open
      onOpenChange={onOpenChange}
      purchaseOrderId={1017}
      deliveryId={800}
      deliveryNo={2}
      lineNumber={1}
      productCode="CHT0238"
      productName="Chai PET 100ml"
    />,
  )
  return onOpenChange
}

/** ai-CR-240 — link trợ lý AI `?delivery=<id>&attach=1` mở thẳng hộp đính tệp của lần giao. */
describe('PurchaseOrderDeliveryAttachDialog', () => {
  beforeEach(() => {
    upload.mockReset()
    uploadArgs.length = 0
  })

  it('nói rõ lần giao nào và liệt kê tệp đã đính', () => {
    renderDialog()
    const dialog = screen.getByRole('dialog')
    expect(within(dialog).getByText('Đính tệp vào lần giao số 2')).toBeInTheDocument()
    expect(within(dialog).getByText(/CHT0238 · Chai PET 100ml/)).toBeInTheDocument()
    expect(within(dialog).getByText('hd-6265.pdf')).toBeInTheDocument()
    //  Danh sách chỉ đọc: không có nút xóa / nút Tải thứ hai trong hộp.
    expect(within(dialog).queryByTitle('Xóa tệp')).toBeNull()
  })

  it('thả tệp là tải lên ngay vào đúng lần giao của đơn', () => {
    renderDialog()
    const file = new File(['x'], 'hoa-don.pdf', { type: 'application/pdf' })
    fireEvent.drop(screen.getByRole('button', { name: /Kéo thả tệp hóa đơn/ }), {
      dataTransfer: { files: [file] },
    })
    expect(upload).toHaveBeenCalledWith({ files: [file] })
    expect(uploadArgs[0]).toEqual(['delivery', 800, 1017])
  })

  it('nút Đóng đóng hộp', async () => {
    const onOpenChange = renderDialog()
    await userEvent.click(screen.getByRole('button', { name: 'Đóng' }))
    expect(onOpenChange).toHaveBeenCalledWith(false)
  })
})
