// duoc-CR-723 — viên số chờ duyệt trên menu Thu mua. Chặn ở tầng `@/core/api` (luật testing.md) để thấy đúng
// đường API được gọi và gọi mấy lần.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type * as CoreApi from '@/core/api'

import {
  PurchaseOrderPendingNavBadge,
  PurchaseRequestPendingNavBadge,
  SurveyPendingNavBadge,
  SurveyRequestPendingNavBadge,
} from './procurement-pending-nav-badge'

const getCalls: string[] = []
let counts: Record<string, number> = {}

vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<typeof CoreApi>()
  return {
    ...actual,
    apiGet: async (url: string) => {
      getCalls.push(url)
      return counts
    },
  }
})

function renderWithProviders(ui: ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  getCalls.length = 0
  counts = {}
})

describe('procurement pending nav badges', () => {
  it('shows each menu item its own pending count from one shared request', async () => {
    counts = { survey_request: 9, purchase_request: 1, purchase_order: 2, survey: 6 }
    renderWithProviders(
      <>
        <SurveyRequestPendingNavBadge />
        <PurchaseRequestPendingNavBadge />
        <PurchaseOrderPendingNavBadge />
        <SurveyPendingNavBadge />
      </>,
    )

    expect(await screen.findByLabelText('9 phiếu đang chờ duyệt')).toHaveTextContent('9')
    expect(screen.getByLabelText('1 phiếu đang chờ duyệt')).toBeInTheDocument()
    expect(screen.getByLabelText('2 phiếu đang chờ duyệt')).toBeInTheDocument()
    expect(screen.getByLabelText('6 phiếu đang chờ duyệt')).toBeInTheDocument()
    //  Bốn viên số, MỘT lượt gọi — không được bắn bốn yêu cầu mỗi lần vẽ menu / đổi trang.
    await waitFor(() => expect(getCalls).toEqual(['/api/dashboard/menu-badges']))
  })

  it('renders nothing for zero or for a key the user cannot read', async () => {
    //  Không có quyền đọc YCMH thì backend bỏ hẳn khóa `purchase_request`.
    counts = { purchase_order: 0 }
    const { container } = renderWithProviders(
      <>
        <PurchaseOrderPendingNavBadge />
        <PurchaseRequestPendingNavBadge />
      </>,
    )

    await waitFor(() => expect(getCalls.length).toBeGreaterThan(0))
    expect(container).toBeEmptyDOMElement()
  })

  it('caps large counts at 99+ so the pill never pushes the label', async () => {
    counts = { purchase_order: 150 }
    renderWithProviders(<PurchaseOrderPendingNavBadge />)

    expect(await screen.findByLabelText('150 phiếu đang chờ duyệt')).toHaveTextContent('99+')
  })
})
