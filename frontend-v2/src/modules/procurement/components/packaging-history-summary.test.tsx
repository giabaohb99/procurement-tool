import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { PackagingHistoryStats } from '../types/packaging-cost-types'
import { PackagingHistorySummary } from './packaging-history-summary'

const STATS: PackagingHistoryStats = {
  purchase_count: 45,
  priced_count: 45,
  qty_total: 186450,
  weighted_avg: 2456.3782,
  min: 2377,
  max: 2500,
  supplier_count: 2,
  first_date: '2025-01-06',
  last_date: '2025-11-07',
}

describe('PackagingHistorySummary', () => {
  it('renders nothing before the first answer', () => {
    const { container } = render(<PackagingHistorySummary stats={undefined} singleCode={false} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('shows the single-code KPIs as cards', () => {
    render(<PackagingHistorySummary stats={STATS} singleCode />)
    expect(screen.getByText('Giá BQ gia quyền')).toBeInTheDocument()
    expect(screen.getByText('2.456,38')).toBeInTheDocument()
    expect(screen.getByText('186.450')).toBeInTheDocument()
    expect(screen.getByText('06/01/2025 – 07/11/2025')).toBeInTheDocument()
  })

  it('hides price KPIs for many codes and explains why', () => {
    render(<PackagingHistorySummary stats={STATS} singleCode={false} />)
    expect(screen.queryByText('Giá BQ gia quyền')).not.toBeInTheDocument()
    expect(screen.getByText(/chọn đúng một mã/i)).toBeInTheDocument()
  })

  it('does not nag about "pick one code" when there is nothing to show (edge: zero purchases)', () => {
    render(
      <PackagingHistorySummary
        stats={{ ...STATS, purchase_count: 0, priced_count: 0, first_date: null, last_date: null }}
        singleCode={false}
      />,
    )
    expect(screen.queryByText(/chọn đúng một mã/i)).not.toBeInTheDocument()
  })
})
