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
  amount_total: 457991000,
  code_count: 1,
  product_count: 0,
  unit: 'Cái',
  first_price: 2377,
  last_price: 2500,
}

describe('PackagingHistorySummary', () => {
  it('renders nothing before the first answer', () => {
    const { container } = render(
      <PackagingHistorySummary stats={undefined} singleCode={false} mode="code" selectedCount={0} />,
    )
    expect(container).toBeEmptyDOMElement()
  })

  it('shows the six template cards for one code, each with its sub-line', () => {
    render(<PackagingHistorySummary stats={STATS} singleCode mode="code" selectedCount={1} />)
    expect(screen.getByText('Tổng giá trị mua')).toBeInTheDocument()
    expect(screen.getByText('457.991.000')).toBeInTheDocument()
    expect(screen.getByText('2.377 – 2.500')).toBeInTheDocument()
    expect(screen.getByText('BQ gia quyền 2.456,38')).toBeInTheDocument()
    expect(screen.getByText('+5,2%')).toBeInTheDocument()
    expect(screen.getByText('06/01/2025 → 07/11/2025')).toBeInTheDocument()
  })

  it('hides price cards for many codes', () => {
    render(
      <PackagingHistorySummary stats={STATS} singleCode={false} mode="code" selectedCount={3} />,
    )
    expect(screen.queryByText('Giá thấp nhất – cao nhất')).not.toBeInTheDocument()
    expect(screen.getByText('Số mã đã chọn')).toBeInTheDocument()
  })
})
