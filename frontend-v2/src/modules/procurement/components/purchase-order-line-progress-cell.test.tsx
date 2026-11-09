import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type { PurchaseOrderItem } from '../types/purchase-order-detail'
import { PurchaseOrderLineProgressCell } from './purchase-order-line-progress-cell'

function item(overrides: Partial<PurchaseOrderItem> = {}) {
  return { id: 9, product_code: 'ABA36', progress_status: 'ordered', ...overrides } as PurchaseOrderItem
}

/** Cụm nút tiến độ dòng — dùng chung cho bảng và hộp chi tiết dòng (duoc-CR-741). */
describe('PurchaseOrderLineProgressCell', () => {
  it('offers Tạm ngưng and Hủy on a running line and reports which one was pressed', async () => {
    const onProgressChange = vi.fn()
    const line = item()
    render(<PurchaseOrderLineProgressCell item={line} controllable onProgressChange={onProgressChange} />)
    await userEvent.click(screen.getByRole('button', { name: 'Tạm ngưng' }))
    await userEvent.click(screen.getByRole('button', { name: 'Hủy' }))
    expect(onProgressChange.mock.calls).toEqual([
      [line, 'paused'],
      [line, 'cancelled'],
    ])
    expect(screen.queryByRole('button', { name: 'Tiếp tục' })).toBeNull()
  })

  it('offers only Tiếp tục on a paused line and shows the pause reason', async () => {
    const onProgressChange = vi.fn()
    const line = item({ progress_status: 'paused', pause_reason: 'NCC hết hàng' })
    render(<PurchaseOrderLineProgressCell item={line} controllable onProgressChange={onProgressChange} />)
    await userEvent.click(screen.getByRole('button', { name: 'Tiếp tục' }))
    expect(onProgressChange).toHaveBeenCalledWith(line, '__resume__')
    expect(screen.getByText('Lý do: NCC hết hàng')).toBeInTheDocument()
  })

  //  Đúng điều kiện v1: lý do chỉ hiện khi dòng ĐANG ngưng / hủy. Dòng đã Tiếp tục vẫn mang
  //  `pause_reason` cũ — hiện ra là người đọc tưởng dòng còn đang ngưng.
  it('shows the reason on a cancelled line, hides the stale one after resuming', () => {
    const { rerender } = render(
      <PurchaseOrderLineProgressCell
        item={item({ progress_status: 'cancelled', pause_reason: 'Đổi NCC' })}
        controllable={false}
      />,
    )
    expect(screen.getByText('Lý do: Đổi NCC')).toBeInTheDocument()

    rerender(
      <PurchaseOrderLineProgressCell
        item={item({ progress_status: 'ordered', pause_reason: 'Đổi NCC' })}
        controllable={false}
      />,
    )
    expect(screen.queryByText(/Lý do:/)).toBeNull()
  })

  it('shows the badge alone when the line cannot be controlled', () => {
    render(<PurchaseOrderLineProgressCell item={item()} controllable={false} />)
    expect(screen.queryByRole('button')).toBeNull()
  })
})
