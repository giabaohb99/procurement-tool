import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type { PurchaseOrderItem } from '../types/purchase-order-detail'
import { PurchaseOrderItemCard } from './purchase-order-item-card'

function item(overrides: Partial<PurchaseOrderItem> = {}): PurchaseOrderItem {
  return {
    id: 501,
    product_code: 'ABA36',
    product_name: 'Abamectin 3.6EC',
    invoice_name: '',
    item_group: 'Thuốc BVTV',
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
    qty_order: 12_000,
    price: 9_500,
    vat: 0,
    warehouse_code: '',
    note: '',
    currency: '',
    exchange_rate: 0,
    weight_kg: 0,
    dimension: '',
    deliveries: [],
    ...overrides,
  }
}

function renderCard(props: Partial<Parameters<typeof PurchaseOrderItemCard>[0]> = {}) {
  return render(
    <PurchaseOrderItemCard
      item={item()}
      index={0}
      amount={<span>114.000.000 đ</span>}
      progress={<span>Đang giao</span>}
      actions={<button type="button">Xóa dòng</button>}
      {...props}
    />,
  )
}

describe('PurchaseOrderItemCard', () => {
  it('leads with the product name, shows the code, quantity × price and the full amount', () => {
    renderCard()

    expect(screen.getByText('Abamectin 3.6EC')).toBeInTheDocument()
    expect(screen.getByText('ABA36')).toBeInTheDocument()
    expect(screen.getByText('Thuốc BVTV', { exact: false })).toBeInTheDocument()
    expect(screen.getByText('12.000 Lít × 9.500')).toBeInTheDocument()
    expect(screen.getByText('114.000.000 đ')).toBeInTheDocument()
  })

  it('falls back to the code, then to a placeholder, when the line has no name yet', () => {
    const { unmount } = renderCard({ item: item({ product_name: '' }) })
    expect(screen.getAllByText('ABA36')).toHaveLength(2)
    unmount()

    renderCard({ item: item({ product_name: '', product_code: '' }) })
    expect(screen.getByText('(chưa chọn hàng)')).toBeInTheDocument()
  })

  it('opens the line detail from the tap area while action buttons stay outside it', async () => {
    const onOpenDetail = vi.fn()
    renderCard({ onOpenDetail })

    const tap = screen.getByRole('button', { name: /Chi tiết dòng 1/ })
    // Lồng nút trong nút là HTML sai: nút Xóa và cụm tiến độ phải là anh em.
    expect(within(tap).queryByRole('button')).toBeNull()
    expect(within(tap).queryByText('Đang giao')).toBeNull()

    await userEvent.click(tap)
    expect(onOpenDetail).toHaveBeenCalledTimes(1)
  })

  it('renders no tap button at all when there is no detail dialog to open', () => {
    renderCard({ onOpenDetail: undefined })
    expect(screen.queryByRole('button', { name: /Chi tiết dòng/ })).toBeNull()
  })

  it('hides "received 0/x" on fresh lines but always flags a short delivery', () => {
    const { unmount } = renderCard({ item: item({ qty_received: 0 }) })
    expect(screen.queryByText(/Nhận /)).toBeNull()
    unmount()

    renderCard({ item: item({ qty_received: 0, is_short_delivery: true }) })
    expect(screen.getByText('Nhận 0/12.000')).toBeInTheDocument()
    expect(screen.getByText('Giao thiếu')).toBeInTheDocument()
  })

  it('shows the VND conversion only when the page passes one (import orders)', () => {
    const { unmount } = renderCard()
    expect(screen.queryByText(/Quy đổi/)).toBeNull()
    unmount()

    renderCard({ baseAmount: <span>2.500.000 đ</span> })
    expect(screen.getByText('2.500.000 đ')).toBeInTheDocument()
  })

  it('locks the bulk-delete tick on a completed line and explains why', async () => {
    const onToggle = vi.fn()
    const { unmount } = renderCard({ selection: { checked: false, onToggle } })
    await userEvent.click(screen.getByRole('checkbox', { name: 'Chọn dòng 1' }))
    expect(onToggle).toHaveBeenCalledTimes(1)
    unmount()

    renderCard({
      selection: { checked: false, disabledReason: 'Dòng đã hoàn thành', onToggle },
    })
    const locked = screen.getByRole('checkbox', { name: 'Chọn dòng 1' })
    expect(locked).toBeDisabled()
    expect(locked).toHaveAttribute('title', 'Dòng đã hoàn thành')
  })
})
