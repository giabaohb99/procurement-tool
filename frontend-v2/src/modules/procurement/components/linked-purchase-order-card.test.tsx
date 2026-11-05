import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { appRoutes } from '@/shared/constants/app-routes'
import { LinkedPurchaseOrderCard, type LinkedPurchaseOrder } from './linked-purchase-order-card'

function order(overrides: Partial<LinkedPurchaseOrder> = {}): LinkedPurchaseOrder {
  return {
    id: 91,
    code: 'DMH-2026-091',
    supplier_name: 'CÔNG TY A',
    supplier_code: 'NCC-A',
    order_date: '2026-09-10',
    amount: 1_500_000,
    status: 'approved',
    ...overrides,
  }
}

function renderCard(row: LinkedPurchaseOrder) {
  return render(
    <MemoryRouter>
      <LinkedPurchaseOrderCard order={row} />
    </MemoryRouter>,
  )
}

describe('LinkedPurchaseOrderCard', () => {
  it('leads with the supplier, links the order code and prints the full amount', () => {
    renderCard(order())

    expect(screen.getByText('CÔNG TY A')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /DMH-2026-091/ })).toHaveAttribute(
      'href',
      appRoutes.procurement.purchaseOrderDetail(91),
    )
    //  Không rút gọn thành "1,5 tr" — người đọc đối chiếu với tổng tiền của phiếu.
    expect(screen.getByText('1.500.000 đ')).toBeInTheDocument()
  })

  it('falls back to the supplier code, then to "Chưa có NCC"', () => {
    const { rerender } = renderCard(order({ supplier_name: '' }))
    expect(screen.getByText('NCC-A')).toBeInTheDocument()

    rerender(
      <MemoryRouter>
        <LinkedPurchaseOrderCard order={order({ supplier_name: '', supplier_code: '' })} />
      </MemoryRouter>,
    )
    expect(screen.getByText('Chưa có NCC')).toBeInTheDocument()
  })

  it('a zero-value order still shows "0 đ" instead of an empty amount', () => {
    renderCard(order({ amount: 0 }))

    expect(screen.getByText('0 đ')).toBeInTheDocument()
  })
})
