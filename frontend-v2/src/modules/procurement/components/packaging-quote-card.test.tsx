import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { PackagingQuote } from '../types/packaging-cost-types'
import { PackagingQuoteCard } from './packaging-quote-card'

describe('PackagingQuoteCard', () => {
  it('shows code, name, unit price and the quote fields without any link (the card itself opens the form)', () => {
    const quote = {
      id: 3,
      product_code: 'CET0028',
      product_name: 'Chai PAPE tròn cổ 43',
      supplier_code: 'NCC01',
      supplier_name: 'Công ty Bao Bì',
      price: 3500.5,
      vat: 8,
      valid_from: '2026-11-20',
      note: 'Giá tháng 11',
      source_type: 1,
      source_id: 0,
    } as PackagingQuote
    render(<PackagingQuoteCard row={quote} />)
    expect(screen.getByText('CET0028')).toBeInTheDocument()
    expect(screen.getByText('3.500,5')).toBeInTheDocument()
    expect(screen.getByText('Công ty Bao Bì · NCC01')).toBeInTheDocument()
    expect(screen.getByText('20/11/2026')).toBeInTheDocument()
    expect(screen.getByText('Giá tháng 11')).toBeInTheDocument()
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
  })
})
