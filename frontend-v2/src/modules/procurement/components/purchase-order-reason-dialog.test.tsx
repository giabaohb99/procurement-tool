import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { PurchaseOrderReasonDialog } from './purchase-order-reason-dialog'

function renderDialog(props: Partial<Parameters<typeof PurchaseOrderReasonDialog>[0]> = {}) {
  const onConfirm = vi.fn()
  const onClose = vi.fn()
  render(
    <PurchaseOrderReasonDialog
      open
      title="Từ chối đơn"
      description="Đơn bị khóa."
      confirmLabel="Từ chối"
      onClose={onClose}
      onConfirm={onConfirm}
      {...props}
    />,
  )
  return { onConfirm, onClose }
}

/** duoc-CR-741 — nút trong hộp lý do mang tên thao tác như bản v1, nút còn lại là Hủy. */
describe('PurchaseOrderReasonDialog', () => {
  it('names the confirm button after the action and offers Hủy instead of Đóng', () => {
    renderDialog()
    expect(screen.getByRole('heading', { name: 'Từ chối đơn' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Từ chối' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Hủy' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Đóng' })).toBeNull()
  })

  it('keeps the confirm button locked until a non-blank reason is typed, then sends it trimmed', async () => {
    const { onConfirm } = renderDialog()
    const confirm = screen.getByRole('button', { name: 'Từ chối' })
    expect(confirm).toBeDisabled()
    await userEvent.type(screen.getByRole('textbox'), '   ')
    expect(confirm).toBeDisabled()
    await userEvent.type(screen.getByRole('textbox'), ' Sai giá  ')
    await userEvent.click(confirm)
    expect(onConfirm).toHaveBeenCalledWith('Sai giá')
  })

  it('falls back to Xác nhận when no label is given', () => {
    renderDialog({ confirmLabel: undefined })
    expect(screen.getByRole('button', { name: 'Xác nhận' })).toBeInTheDocument()
  })

  it('closes on Hủy without confirming', async () => {
    const { onConfirm, onClose } = renderDialog()
    await userEvent.click(screen.getByRole('button', { name: 'Hủy' }))
    expect(onClose).toHaveBeenCalled()
    expect(onConfirm).not.toHaveBeenCalled()
  })
})
