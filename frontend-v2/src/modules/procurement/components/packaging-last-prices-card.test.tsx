import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import type { PackagingLastPricesRow } from '../types/packaging-cost-types'
import { PackagingLastPricesCard } from './packaging-last-prices-card'

const row: PackagingLastPricesRow = {
  code: 'CET0051',
  name: 'Chai PAPE tròn cổ 43 (45g)',
  group: 'Chai',
  unit: 'Cái',
  purchase_count: 4,
  purchases: [
    { date: '2026-01-22', supplier_code: 'N1', supplier: 'Công ty A', qty: 1000, price: 4600 },
    { date: '2025-05-12', supplier_code: 'N2', supplier: 'Công ty B', qty: 500, price: 5048 },
    { date: '2025-05-08', supplier_code: 'N2', supplier: 'Công ty B', qty: 500, price: 4900 },
  ],
  last_price: 4600,
  last_date: '2026-01-22',
  v12: -0.089,
  v1n: null,
  avg: 4849.33,
}

describe('PackagingLastPricesCard', () => {
  it('folds the n purchase column groups into a vertical list with table colours', () => {
    render(
      <MemoryRouter>
        <PackagingLastPricesCard row={row} n={5} showQty={false} />
      </MemoryRouter>,
    )
    expect(screen.getByRole('link', { name: 'CET0051' })).toBeInTheDocument()
    expect(screen.getByText('Lần 1 so lần 5')).toBeInTheDocument()
    expect(screen.getByText('Giá TB 5 lần')).toBeInTheDocument()
    expect(screen.getByText('-8,9%')).toHaveClass('text-destructive')
    expect(screen.getAllByRole('listitem')).toHaveLength(3)
    expect(screen.getByText('22/01/2026')).toBeInTheDocument()
    //  Lần 1 rẻ hơn lần 2 → đỏ; lần 2 đắt hơn lần 3 → xanh; lần cuối không có gì để so.
    expect(screen.getByText('4.600')).toHaveClass('text-destructive')
    expect(screen.getByText('5.048')).toHaveClass('text-emerald-600')
    expect(screen.queryByText(/^SL /)).not.toBeInTheDocument()
  })

  it('shows quantities when the toolbar switch is on and cuts the list at n', () => {
    render(
      <MemoryRouter>
        <PackagingLastPricesCard row={row} n={2} showQty />
      </MemoryRouter>,
    )
    expect(screen.getAllByRole('listitem')).toHaveLength(2)
    expect(screen.getByText('SL 1.000')).toBeInTheDocument()
  })
})
