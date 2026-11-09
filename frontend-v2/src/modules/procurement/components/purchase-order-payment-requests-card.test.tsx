import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { PaymentRequestSummary } from '@/modules/finance/types/payment-request'
import { PurchaseOrderPaymentRequestsCard } from './purchase-order-payment-requests-card'

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => true }),
}))

function request(overrides: Partial<PaymentRequestSummary> = {}): PaymentRequestSummary {
  return {
    id: 77,
    code: 'YCTT-0077',
    supplier_code: 'CH',
    supplier_name: 'Bao bì Cẩm Hùng',
    company_id: 1,
    source_type: 'goods',
    request_date: '2026-10-05',
    payment_method: 'transfer',
    prepay: 0,
    total: 28_620_000,
    note: '',
    reject_reason: '',
    status: 'draft',
    misa_code: '',
    created_by_name: 'Nguyễn Văn A',
    ...overrides,
  }
}

let items: PaymentRequestSummary[] = []
vi.mock('@/modules/finance/hooks/use-payment-requests', () => ({
  usePaymentRequests: () => ({ data: { items, total: items.length } }),
}))

function renderCard() {
  return render(
    <MemoryRouter>
      <PurchaseOrderPaymentRequestsCard poCode="PO-1" />
    </MemoryRouter>,
  )
}

/** duoc-CR-720 — khổ điện thoại: bảng YCTT liên quan thành thẻ bấm được. */
describe('PurchaseOrderPaymentRequestsCard — khổ điện thoại', () => {
  beforeEach(() => {
    vi.stubGlobal('matchMedia', (query: string) => ({
      matches: true,
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }))
  })
  afterEach(() => {
    vi.unstubAllGlobals()
    items = []
  })

  it('renders one link card per request, leading with the supplier and keeping the full amount', () => {
    items = [request(), request({ id: 78, code: 'YCTT-0078', prepay: 1 })]
    const { container } = renderCard()

    expect(container.querySelector('table')).toBeNull()
    const links = screen.getAllByRole('link')
    expect(links).toHaveLength(2)
    expect(links[0]).toHaveAttribute('href', expect.stringContaining('77'))
    expect(screen.getAllByText('Bao bì Cẩm Hùng')).toHaveLength(2)
    expect(screen.getAllByText('28.620.000 đ')).toHaveLength(2)
    // Huy hiệu Trả trước của bảng không được rơi mất ở thẻ.
    expect(screen.getAllByText('Trả trước')).toHaveLength(1)
  })

  it('still hides the whole block when the order has no request', () => {
    const { container } = renderCard()
    expect(container).toBeEmptyDOMElement()
  })
})
