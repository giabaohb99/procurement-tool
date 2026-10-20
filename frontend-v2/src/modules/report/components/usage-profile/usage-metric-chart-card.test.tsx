import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import type { UsageMetricCatalogItem } from '../../types/usage-metric-catalog'
import { UsageMetricChartCard } from './usage-metric-chart-card'

//  recharts cần đo kích thước — jsdom không có, thay bằng khung ghi lại dữ liệu nhận được.
vi.mock('./usage-metric-histogram', () => ({
  UsageMetricHistogram: (p: { buckets: unknown[]; medianText: string }) => (
    <div data-testid="histogram">{p.buckets.length} cột · {p.medianText}</div>
  ),
}))
vi.mock('./usage-metric-trend', () => ({
  UsageMetricTrend: (p: { points: unknown[] }) => <div data-testid="trend">{p.points.length} điểm</div>,
}))

const base: UsageMetricCatalogItem = {
  key: 'logins', section: '3.1', unit: 'count', phase: 1, direction: -1, measured_users: 8, total_users: 10,
  company_median: 5, unmeasured_reason: null,
  histogram: [{ lo: 0, hi: 5, count: 3 }, { lo: 5, hi: null, count: 5 }],
  trend: [{ week: '2026-10-05', median: 4, measured: 7 }, { week: '2026-10-12', median: 5, measured: 8 }],
}

const renderCard = (item: UsageMetricCatalogItem, hasWeek = true) =>
  render(<MemoryRouter><UsageMetricChartCard item={item} hasWeek={hasWeek} /></MemoryRouter>)

describe('UsageMetricChartCard', () => {
  it('renders header summary, histogram, trend and the ranking link', () => {
    renderCard(base)
    expect(screen.getByText('Lượt đăng nhập')).toBeInTheDocument()
    expect(screen.getByText(/8\/10 người · trung vị 5 · tốt khi thấp/)).toBeInTheDocument()
    expect(screen.getByTestId('histogram')).toHaveTextContent('2 cột · Trung vị 5')
    expect(screen.getByTestId('trend')).toHaveTextContent('2 điểm')
    expect(screen.getByRole('link', { name: /Xem xếp hạng/ })).toHaveAttribute('href', expect.stringContaining('metric=logins'))
    expect(screen.queryByText('Mới có 1 tuần số liệu')).not.toBeInTheDocument()
  })

  it('says only one week of data exists and still draws the single point', () => {
    renderCard({ ...base, trend: [base.trend[1]] })
    expect(screen.getByText('Mới có 1 tuần số liệu')).toBeInTheDocument()
    expect(screen.getByTestId('trend')).toHaveTextContent('1 điểm')
  })

  it('unmeasured card has a reason, no charts and no ranking link', () => {
    renderCard({ ...base, measured_users: 0, company_median: null, unmeasured_reason: 3, histogram: [], trend: [] })
    expect(screen.getByText('Không áp dụng')).toBeInTheDocument()
    expect(screen.queryByTestId('histogram')).not.toBeInTheDocument()
    expect(screen.queryByTestId('trend')).not.toBeInTheDocument()
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
  })

  it('shows «Chưa thu thập» when there is no snapshot week at all', () => {
    renderCard({ ...base, measured_users: 0, company_median: null, histogram: [], trend: [] }, false)
    expect(screen.getByText('Chưa thu thập')).toBeInTheDocument()
  })

  it('info button opens meaning / formula / source', async () => {
    renderCard(base)
    await userEvent.click(screen.getByRole('button', { name: /Xem định nghĩa/ }))
    expect(await screen.findByText('Ý nghĩa')).toBeInTheDocument()
    expect(screen.getByText('Cách tính')).toBeInTheDocument()
    expect(screen.getByText('Nguồn dữ liệu')).toBeInTheDocument()
  })
})
