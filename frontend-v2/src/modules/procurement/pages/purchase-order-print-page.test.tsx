import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type * as ReactRouterModule from 'react-router-dom'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

type ReactRouter = typeof ReactRouterModule

import type { PurchaseOrderPrintData } from '../api/purchase-order-api'
import { PurchaseOrderPrintPage } from './purchase-order-print-page'

const printData = vi.hoisted(() => ({ current: null as unknown }))

vi.mock('../hooks/use-purchase-order', () => ({
  usePurchaseOrderPrintData: () => ({
    data: printData.current,
    isLoading: false,
    isError: printData.current === null,
  }),
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<ReactRouter>('react-router-dom')
  return { ...actual, useParams: () => ({ id: '7' }) }
})

function makeData(overrides: Partial<PurchaseOrderPrintData> = {}): PurchaseOrderPrintData {
  return {
    id: 7,
    code: 'PO-2026-0007',
    order_date: '2026-08-31',
    supplier_name: 'NCC Một',
    items: [],
    company: {},
    supplier: {},
    warehouse: {},
    wh_names: {},
    signers: {
      creator_name: 'Nguyen Van Lap',
      creator_signature: 'https://cdn/ky-lap.png',
      approver_name: 'Tran Thi Duyet',
      approver_signature: 'https://cdn/ky-duyet.png',
    },
    ...overrides,
  } as PurchaseOrderPrintData
}

function renderPage(data: PurchaseOrderPrintData | null) {
  printData.current = data
  return render(
    <MemoryRouter>
      <PurchaseOrderPrintPage />
    </MemoryRouter>,
  )
}

describe('PurchaseOrderPrintPage — công tắc chữ ký', () => {
  it('shows both signature images by default', () => {
    renderPage(makeData())

    expect(screen.getByAltText('Chữ ký Người lập')).toHaveAttribute('src', 'https://cdn/ky-lap.png')
    expect(screen.getByAltText('Chữ ký Trưởng bộ phận')).toHaveAttribute(
      'src',
      'https://cdn/ky-duyet.png',
    )
  })

  it('drops the images but keeps the names when switching to "Không chữ ký"', async () => {
    const user = userEvent.setup()
    renderPage(makeData())

    await user.click(screen.getByRole('button', { name: 'Không chữ ký' }))

    expect(screen.queryByAltText('Chữ ký Người lập')).not.toBeInTheDocument()
    expect(screen.queryByAltText('Chữ ký Trưởng bộ phận')).not.toBeInTheDocument()
    // Họ tên vẫn phải in: ô ghi "(Ký, ghi rõ họ tên)", bỏ tên đi thì người ký tay
    // không biết ô đó là của ai.
    expect(screen.getByText('Nguyen Van Lap')).toBeInTheDocument()
    expect(screen.getByText('Tran Thi Duyet')).toBeInTheDocument()
  })

  it('keeps the signature choice when switching between the two forms', async () => {
    const user = userEvent.setup()
    renderPage(makeData())

    await user.click(screen.getByRole('button', { name: 'Không chữ ký' }))
    await user.click(screen.getByRole('button', { name: 'Đơn mua hàng (nội bộ)' }))

    expect(screen.queryByAltText('Chữ ký Người lập')).not.toBeInTheDocument()
    expect(screen.getByText('Trưởng phòng / Trưởng BP')).toBeInTheDocument()
  })

  it('leaves the "Người nhận" box empty on the internal form — nobody signs it in the system', async () => {
    const user = userEvent.setup()
    renderPage(makeData())

    await user.click(screen.getByRole('button', { name: 'Đơn mua hàng (nội bộ)' }))

    expect(screen.getByText('Người nhận')).toBeInTheDocument()
    expect(screen.queryByAltText('Chữ ký Người nhận')).not.toBeInTheDocument()
  })

  it('renders an unapproved order without an approver signature or name', () => {
    renderPage(
      makeData({
        signers: {
          creator_name: 'Nguyen Van Lap',
          creator_signature: 'https://cdn/ky-lap.png',
          approver_name: '',
          approver_signature: '',
        },
      }),
    )

    expect(screen.getByAltText('Chữ ký Người lập')).toBeInTheDocument()
    expect(screen.queryByAltText('Chữ ký Trưởng bộ phận')).not.toBeInTheDocument()
    // Ô ký vẫn còn để ký tay, chỉ trống ruột.
    expect(screen.getByText('Trưởng bộ phận')).toBeInTheDocument()
  })

  it('renders an old order whose payload carries no signers block at all', () => {
    renderPage(makeData({ signers: undefined }))

    expect(screen.queryByAltText('Chữ ký Người lập')).not.toBeInTheDocument()
    expect(screen.getByText('Người lập')).toBeInTheDocument()
  })
})
