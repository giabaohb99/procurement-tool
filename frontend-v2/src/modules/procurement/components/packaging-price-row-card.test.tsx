import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import type { PackagingPriceRow } from '../types/packaging-cost-types'
import { PackagingPriceRowCard } from './packaging-price-row-card'

const row: PackagingPriceRow = {
  code: 'CET0028',
  name: 'Chai PAPE tròn cổ 43',
  group: 'Chai',
  unit: 'Cái',
  purchase_count: 3,
  last_date: '2026-06-30',
  last_purchase_price: 3170,
  last_purchase_date: '2026-06-30',
  prev_purchase_price: 4300,
  quote: { price: 3500.5, valid_from: '2026-11-20' },
  old: 3170,
  new: 3500.5,
  diff: 330.5,
  pct: 0.104,
  usage: 30,
  min: 3170,
  max: 4724,
  warnings: [],
}

describe('PackagingPriceRowCard', () => {
  it('shows the price-list fields under the table headers', () => {
    render(
      <MemoryRouter>
        <PackagingPriceRowCard row={row} />
      </MemoryRouter>,
    )
    expect(screen.getByRole('link', { name: 'CET0028' })).toBeInTheDocument()
    for (const label of ['Số lần mua', 'Mua gần nhất', 'Giá mua gần nhất', 'Giá mua lần trước', 'Báo giá mới', 'Số SP đang dùng']) {
      expect(screen.getByText(label)).toBeInTheDocument()
    }
    expect(screen.getByText('30/06/2026')).toBeInTheDocument()
    expect(screen.getByText('20/11/2026')).toBeInTheDocument()
    expect(screen.getByText('+330,5')).toHaveClass('text-emerald-600')
    expect(screen.queryByRole('button', { name: 'Báo giá' })).not.toBeInTheDocument()
  })

  it('opens a new quote for the code when the user may quote', () => {
    const onQuote = vi.fn()
    render(
      <MemoryRouter>
        <PackagingPriceRowCard row={row} onQuote={onQuote} />
      </MemoryRouter>,
    )
    fireEvent.click(screen.getByRole('button', { name: 'Báo giá' }))
    expect(onQuote).toHaveBeenCalledWith(row)
  })
})
