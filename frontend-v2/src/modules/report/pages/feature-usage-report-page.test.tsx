import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { apiGet } from '@/core/api'
import { UI_ACTION_CODE } from '@/core/telemetry/ui-event-codes'

import type { FeatureSummary } from '../types/feature-usage'
import { FeatureUsageReportPage } from './feature-usage-report-page'

vi.mock('@/core/api', () => ({ apiGet: vi.fn(), downloadFile: vi.fn(), extractErrorMessage: () => 'lỗi' }))
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => false }),
  useNavContext: () => ({}),
}))
vi.mock('@/modules/hr/hooks/use-departments', () => ({ useDepartments: () => ({ data: { items: [] } }) }))
vi.mock('@/modules/hr/hooks/use-companies', () => ({ useCompanies: () => ({ data: { items: [] } }) }))

const empty: FeatureSummary = {
  period: { date_from: '2026-09-21', date_to: '2026-10-20' },
  tracking_since: null,
  has_data: false,
  active_users: 0,
  actions: [], forms: [], screens: [], searches: [], errors: [],
  unused_actions: [1, 2],
  unused_forms: [1],
}

const withData: FeatureSummary = {
  ...empty,
  tracking_since: '2026-10-01',
  has_data: true,
  active_users: 10,
  actions: [{ kind: 1, code: UI_ACTION_CODE.EXPORT_EXCEL, route: '/procurement/requests', users: 4, uses: 9, completes: 0, abandons: 0, fails: 0, duration_ms: 0 }],
  forms: [{ kind: 2, code: 1, route: '', users: 3, uses: 10, completes: 6, abandons: 4, fails: 0, duration_ms: 60000 }],
  errors: [{ kind: 5, code: 0, route: '/procurement/orders', users: 2, uses: 5, completes: 0, abandons: 0, fails: 0, duration_ms: 0 }],
  unused_actions: [UI_ACTION_CODE.PRINT],
  unused_forms: [],
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={['/report/feature-usage']}>
        <FeatureUsageReportPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => vi.mocked(apiGet).mockReset())

describe('FeatureUsageReportPage (duoc-CR-655)', () => {
  it('shows the "chưa thu thập" banner and no "unused" claims when there is no data', async () => {
    vi.mocked(apiGet).mockResolvedValue(empty)
    renderPage()
    expect(await screen.findByText(/Chưa thu thập — kỳ này chưa có thao tác nào/)).toBeInTheDocument()
    expect(screen.queryByText(/Chức năng chưa ai dùng trong kỳ/)).not.toBeInTheDocument()
  })

  it('renders usage, the unused list and the form abandon rate from the aggregated data', async () => {
    vi.mocked(apiGet).mockResolvedValue(withData)
    renderPage()
    expect(await screen.findByText('Chức năng nhiều người dùng nhất')).toBeInTheDocument()
    expect(screen.getAllByText('Xuất Excel').length).toBeGreaterThan(0)
    expect(screen.getByText('In')).toBeInTheDocument()   // nằm trong danh sách «chưa ai dùng»
    expect(screen.getByText(/Số liệu chỉ có từ ngày/)).toBeInTheDocument()
    expect(screen.queryByText(/Chưa thu thập — kỳ này/)).not.toBeInTheDocument()
  })

  it('calls the summary endpoint with the default period and never asks for per-person data', async () => {
    vi.mocked(apiGet).mockResolvedValue(withData)
    renderPage()
    await screen.findByText('Chức năng nhiều người dùng nhất')
    const [url, config] = vi.mocked(apiGet).mock.calls[0]
    expect(url).toBe('/api/feature-usage/summary')
    expect(config).toEqual({ params: { preset: 'last_30_days' } })
  })
})
