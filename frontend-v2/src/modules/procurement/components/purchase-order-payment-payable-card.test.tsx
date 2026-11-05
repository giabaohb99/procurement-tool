import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type { Payable } from '../api/purchase-order-payment-api'
import { PurchaseOrderPaymentPayableCard } from './purchase-order-payment-payable-card'

function payable(overrides: Partial<Payable> = {}): Payable {
  return {
    id: 41,
    supplier_code: 'CH',
    supplier_name: 'Bao bì Cẩm Hùng',
    source_type: 'goods',
    po_code: 'PO-1',
    invoice_no: 'HD-009',
    incur_date: '2026-03-01',
    due_date: '2026-03-31',
    total: 28_620_000,
    paid_amount: 8_620_000,
    remaining: 20_000_000,
    status: 'unpaid',
    ...overrides,
  }
}

describe('PurchaseOrderPaymentPayableCard', () => {
  it('shows supplier, invoice, date and the three money figures in full', () => {
    render(
      <PurchaseOrderPaymentPayableCard
        payable={payable()}
        supplierLabel="Nhà cung cấp"
        checked={false}
        onCheckedChange={vi.fn()}
      />,
    )
    expect(screen.getByText('Nhà cung cấp')).toBeInTheDocument()
    expect(screen.getByText('Bao bì Cẩm Hùng')).toBeInTheDocument()
    expect(screen.getByText('HD-009')).toBeInTheDocument()
    expect(screen.getByText('01/03/2026')).toBeInTheDocument()
    expect(screen.getByText('28.620.000 đ')).toBeInTheDocument()
    expect(screen.getByText('8.620.000 đ')).toBeInTheDocument()
    expect(screen.getByText('20.000.000 đ')).toBeInTheDocument()
  })

  it('ticks when the user taps the card text, not only the 16px box', async () => {
    const onCheckedChange = vi.fn()
    render(
      <PurchaseOrderPaymentPayableCard
        payable={payable()}
        supplierLabel="Nhà cung cấp"
        checked={false}
        onCheckedChange={onCheckedChange}
      />,
    )
    await userEvent.click(screen.getByText('Bao bì Cẩm Hùng'))
    expect(onCheckedChange).toHaveBeenCalledWith(true)
  })

  it('falls back to the payable id when the invoice number is empty', () => {
    render(
      <PurchaseOrderPaymentPayableCard
        payable={payable({ invoice_no: '', supplier_name: '' })}
        supplierLabel="Đơn vị vận chuyển"
        checked
        onCheckedChange={vi.fn()}
      />,
    )
    expect(screen.getByRole('checkbox', { name: 'Chọn hóa đơn 41' })).toBeChecked()
    // Tab cước vận chuyển: bên nhận là nhà xe, không phải NCC sản xuất.
    expect(screen.getByText('Đơn vị vận chuyển')).toBeInTheDocument()
    expect(screen.getByText('CH')).toBeInTheDocument()
  })
})
