import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type { PurchaseOrderDelivery } from '../types/purchase-order-detail'
import { PurchaseOrderDeliveryCard } from './purchase-order-delivery-card'

function delivery(overrides: Partial<PurchaseOrderDelivery> = {}): PurchaseOrderDelivery {
  return {
    id: 71,
    delivery_no: 2,
    warehouse_code: 'KHO-HCM',
    carrier_code: '',
    carrier_name: '',
    ship_qty: 0,
    ship_unit: '',
    received_qty: 1_500,
    promised_date: '',
    expected_date: '',
    received_date: '2026-10-03',
    std_days: 0,
    invoice_no: '',
    invoice_date: '',
    shipping_unit_price: 0,
    shipping_amount: 0,
    qc_result: '',
    status: 'received',
    extra_request: '',
    progress_note: '',
    remaining: 3_250_000,
    ...overrides,
  }
}

const FIELDS = [
  { key: 'invoice_no', label: 'Số hóa đơn' },
  { key: 'diff_promise', label: 'Trễ CK' },
]

function renderCard(props: Partial<Parameters<typeof PurchaseOrderDeliveryCard>[0]> = {}) {
  return render(
    <PurchaseOrderDeliveryCard
      delivery={delivery()}
      index={1}
      fields={FIELDS}
      renderField={(key) => (key === 'invoice_no' ? <input aria-label="ô số HĐ" /> : null)}
      receivedAmount={<span>14.250.000 đ</span>}
      status={<span>Đã nhận</span>}
      {...props}
    />,
  )
}

describe('PurchaseOrderDeliveryCard', () => {
  it('summarises the delivery while collapsed: number, status, warehouse, qty, amount, debt', () => {
    renderCard()

    expect(screen.getByText('Lần 2')).toBeInTheDocument()
    expect(screen.getByText('Đã nhận')).toBeInTheDocument()
    expect(screen.getByText('Kho KHO-HCM · Nhận 03/10/2026')).toBeInTheDocument()
    expect(screen.getByText('SL nhận 1.500')).toBeInTheDocument()
    expect(screen.getByText('14.250.000 đ')).toBeInTheDocument()
    expect(screen.getByText('Còn nợ 3.250.000 đ')).toBeInTheDocument()
    // Gập thì chưa dựng ô nhập nào.
    expect(screen.queryByRole('group', { name: 'Số hóa đơn' })).toBeNull()
  })

  it('does not claim a debt for an unsaved delivery (backend has not booked it yet)', () => {
    renderCard({ delivery: delivery({ id: undefined, remaining: 3_250_000 }) })
    expect(screen.queryByText(/Còn nợ/)).toBeNull()
  })

  it('falls back to the position when delivery_no is 0', () => {
    renderCard({ delivery: delivery({ delivery_no: 0 }) })
    expect(screen.getByText('Lần 2')).toBeInTheDocument()
  })

  it('expands into labelled fields rendered by the table and dashes empty ones', async () => {
    renderCard()
    const toggle = screen.getByRole('button', { expanded: false })
    await userEvent.click(toggle)

    expect(toggle).toHaveAttribute('aria-expanded', 'true')
    const invoice = screen.getByRole('group', { name: 'Số hóa đơn' })
    expect(within(invoice).getByRole('textbox', { name: 'ô số HĐ' })).toBeInTheDocument()
    expect(within(screen.getByRole('group', { name: 'Trễ CK' })).getByText('—')).toBeInTheDocument()
  })

  it('opens a freshly added delivery so the user can type right away', () => {
    renderCard({ defaultOpen: true })
    expect(screen.getByRole('group', { name: 'Số hóa đơn' })).toBeInTheDocument()
  })

  it('keeps the delete button as a sibling of the toggle, shown only when removable', async () => {
    const { unmount } = renderCard()
    expect(screen.queryByRole('button', { name: /Xóa lần giao/ })).toBeNull()
    unmount()

    const onRemove = vi.fn()
    renderCard({ onRemove })
    const toggle = screen.getByRole('button', { expanded: false })
    expect(within(toggle).queryByRole('button')).toBeNull()
    await userEvent.click(screen.getByRole('button', { name: 'Xóa lần giao 2' }))
    expect(onRemove).toHaveBeenCalledTimes(1)
  })
})
