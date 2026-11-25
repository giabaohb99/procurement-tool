import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import type { PackagingHistoryRow } from '../types/packaging-cost-types'
import { DiffCell, PriceCell, SourceCell } from './packaging-history-cells'

const row = (over: Partial<PackagingHistoryRow> = {}): PackagingHistoryRow => ({
  id: 1,
  date: '2026-05-01',
  code: 'CPT0105',
  name: 'Chai',
  group: 'Chai',
  supplier_code: 'NCC01',
  supplier: 'Nhựa',
  warehouse: 'Kho DEGO Cần Thơ',
  qty: 100,
  unit: 'Cái',
  price: 130,
  vat: 8,
  amount: 13000,
  source_type: 1,
  line_stage: 2,
  is_open: false,
  doc_id: 0,
  po_code: '',
  prev_price: 120,
  diff: 10,
  pct: 10 / 120,
  seq: 6,
  fg_code: '',
  fg_name: '',
  role: null,
  ...over,
})

const inRouter = (ui: React.ReactElement) => render(<MemoryRouter>{ui}</MemoryRouter>)

describe('PriceCell', () => {
  it('mutes a zero price with an explanation instead of showing it as a real price', () => {
    inRouter(<PriceCell row={row({ price: 0, diff: null })} />)
    expect(screen.getByText('0')).toHaveAttribute('title', expect.stringContaining('không tính'))
  })

  it('shows a normal price in bold', () => {
    inRouter(<PriceCell row={row({ price: 1234.5 })} />)
    expect(screen.getByText('1.234,5')).toHaveClass('font-semibold')
  })
})

describe('DiffCell', () => {
  it('paints an increase green and a decrease red, with the percent', () => {
    const { rerender } = inRouter(<DiffCell row={row()} />)
    expect(screen.getByText('+10 (+8,3%)').className).toMatch(/emerald/)
    rerender(
      <MemoryRouter>
        <DiffCell row={row({ diff: -5, pct: -0.05 })} />
      </MemoryRouter>,
    )
    expect(screen.getByText('-5 (-5,0%)').className).toMatch(/destructive/)
  })

  it('shows a dash for the first purchase, and a plain muted 0 (no percent) for an unchanged price', () => {
    const { rerender } = inRouter(
      <DiffCell row={row({ diff: null, pct: null, prev_price: null })} />,
    )
    expect(screen.getByText('—')).toBeInTheDocument()
    rerender(
      <MemoryRouter>
        <DiffCell row={row({ diff: 0, pct: 0 })} />
      </MemoryRouter>,
    )
    expect(screen.getByText('0').className).not.toMatch(/emerald|destructive/)
  })
})

describe('SourceCell', () => {
  it('marks an open purchase-order line and links its order', () => {
    inRouter(<SourceCell row={row({ source_type: 2, line_stage: 1, is_open: true, doc_id: 77, po_code: 'PO00077' })} />)
    expect(screen.getByText('ĐMH đang mở')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'PO00077' })).toHaveAttribute(
      'href',
      '/procurement/purchase-orders/77',
    )
  })

  it('links a finished order without the badge, and renders nothing for legacy rows without an order', () => {
    const { container, rerender } = inRouter(<SourceCell row={row({ source_type: 2, doc_id: 5, po_code: '' })} />)
    expect(screen.queryByText('ĐMH đang mở')).not.toBeInTheDocument()
    expect(screen.getByRole('link', { name: '#5' })).toBeInTheDocument()
    rerender(
      <MemoryRouter>
        <SourceCell row={row()} />
      </MemoryRouter>,
    )
    expect(container).toBeEmptyDOMElement()
  })
})
