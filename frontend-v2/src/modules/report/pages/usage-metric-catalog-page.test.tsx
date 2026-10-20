import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { apiGet } from '@/core/api'

import { UsageMetricCatalogPage } from './usage-metric-catalog-page'

vi.mock('@/core/api', () => ({ apiGet: vi.fn(), downloadFile: vi.fn(), extractErrorMessage: () => 'lỗi' }))

const item = (key: string, measured: number) => ({
  key, section: '3.1', unit: 'count', phase: 1, direction: 1, measured_users: measured, total_users: 10,
  company_median: measured ? 5 : null, unmeasured_reason: measured ? null : 2,
})

function Where() {
  const l = useLocation()
  return <span data-testid="where">{l.pathname + l.search}</span>
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={['/report/usage-metrics']}>
        <Routes>
          <Route path="/report/usage-metrics" element={<UsageMetricCatalogPage />} />
          <Route path="/report/usage-profiles" element={<Where />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.mocked(apiGet).mockReset()
  vi.mocked(apiGet).mockResolvedValue({ week: '2026-10-12', deferred: [], metrics: [item('logins', 8), item('active_workdays', 0)] })
})

describe('UsageMetricCatalogPage ranking links (duoc-CR-650)', () => {
  it('opens the list sorted by the clicked metric', async () => {
    renderPage()
    await userEvent.click(await screen.findByText('Lượt đăng nhập'))
    await waitFor(() => expect(screen.getByTestId('where')).toHaveTextContent('/report/usage-profiles?metric=logins&sort=-metric'))
  })

  it('does not navigate for a metric nobody has measured and says so', async () => {
    renderPage()
    await userEvent.click(await screen.findByText('Ngày làm việc có vào'))
    expect(screen.queryByTestId('where')).not.toBeInTheDocument()
    expect(screen.getAllByText('Chưa có dữ liệu').length).toBeGreaterThan(0)
  })
})
