import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { apiGet } from '@/core/api'
import type * as CoreApiModule from '@/core/api'
import { TooltipProvider } from '@/shared/ui/tooltip'

import type { ReportAnalyticsResponse, ReportMetricMeta, ReportPageConfig } from '../types/report-analytics'
import type { ReportDrilldownResponse } from '../types/report-drilldown'
import { ReportAnalyticsPage } from './report-analytics-page'

vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<typeof CoreApiModule>()
  return { ...actual, apiGet: vi.fn(), downloadFile: vi.fn() }
})
vi.mock('@/core/authorization/use-permission', () => ({ usePermission: () => ({ can: () => false }) }))

const SUMMARY = '/api/labor-contracts/summary'
const ROWS = '/api/labor-contracts/summary/rows'

function metric(key: string, label: string): ReportMetricMeta {
  return { key, label, kind: 'int', good: null, helper: false, snapshot: false }
}

function summary(drilldown: string[] | undefined): ReportAnalyticsResponse {
  return {
    period: {
      date_from: '2026-10-01', date_to: '2026-10-27', compare_from: null, compare_to: null,
      compare: 'none', granularity: 'day', preset: 'this_month',
    },
    meta: {
      //  `no_contract` CỐ Ý vắng khỏi meta (vd bị gỡ vì quyền) — hàng thẻ không được vỡ.
      metrics: [metric('active', 'Đang hiệu lực'), metric('overdue', 'Đã quá hạn, vẫn đi làm')],
      dimensions: [{ key: 'department', label: 'Phòng ban' }],
      group_by: 'department',
      drilldown_metrics: drilldown,
    },
    totals: { current: { active: 40, overdue: 3 }, compare: null },
    trend: [],
    groups: [
      { key: '5', label: 'Kế toán', current: { active: 30, overdue: 2 }, compare: null },
      { key: '', label: '(Chưa gắn)', current: { active: 8, overdue: 1 }, compare: null },
      { key: '__other__', label: '(Các nhóm khác — 3 nhóm)', current: { active: 2, overdue: 0 }, compare: null },
    ],
    notes: [],
  }
}

const ROWS_RESPONSE: ReportDrilldownResponse = {
  metric: { key: 'overdue', label: 'Đã quá hạn, vẫn đi làm' },
  columns: [{ key: 'employee_name', label: 'Họ tên', kind: 'text' }],
  rows: [{ employee_name: 'Lê Thị C' }],
  total: 1,
  truncated: false,
}

const CONFIG: ReportPageConfig = {
  endpoint: SUMMARY,
  drilldownEndpoint: ROWS,
  entity: 'labor_contract',
  title: 'Hợp đồng lao động',
  description: 'Mô tả.',
  slug: 'labor-contract-test',
  kpis: ['active', 'overdue', 'no_contract'],
  chartMetric: 'active',
  defaultGroupBy: 'department',
}

let drilldownMetrics: string[] | undefined
beforeEach(() => {
  localStorage.clear()
  drilldownMetrics = ['overdue']
  vi.mocked(apiGet).mockReset()
  vi.mocked(apiGet).mockImplementation(async (url) =>
    (url === ROWS ? ROWS_RESPONSE : summary(drilldownMetrics)) as never,
  )
})

function renderPage(config: ReportPageConfig = CONFIG, url = '/report/labor-contract') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[url]}>
        <TooltipProvider>
          <ReportAnalyticsPage config={config} />
        </TooltipProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const rowsCalls = () => vi.mocked(apiGet).mock.calls.filter(([u]) => u === ROWS)
const lastRowsParams = () => (rowsCalls().at(-1)?.[1] as { params: Record<string, string> }).params

describe('ReportAnalyticsPage — drilldown', () => {
  it('puts «Xem danh sách» only on drillable KPI cards and skips KPIs missing from meta', async () => {
    renderPage()
    expect(await screen.findByRole('button', { name: 'Xem danh sách Đã quá hạn, vẫn đi làm' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Xem danh sách Đang hiệu lực' })).not.toBeInTheDocument()
    expect(screen.queryByText('no_contract')).not.toBeInTheDocument()
    //  Mở trang KHÔNG tốn lượt `/rows` nào.
    expect(rowsCalls()).toHaveLength(0)
  })

  it('opens the whole list from a KPI card with group_by=none and the page filters', async () => {
    const user = userEvent.setup()
    renderPage(CONFIG, '/report/labor-contract?department_id=7')
    await user.click(await screen.findByRole('button', { name: 'Xem danh sách Đã quá hạn, vẫn đi làm' }))
    expect(await screen.findByText('Lê Thị C')).toBeInTheDocument()
    expect(lastRowsParams()).toMatchObject({ metric: 'overdue', group_by: 'none', department_id: '7' })
    expect(lastRowsParams()).not.toHaveProperty('group_key')
  })

  it('opens a group list from its row, sending "" for «(Chưa gắn)», and has no button on __other__', async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findByRole('button', { name: 'Xem danh sách Kế toán' })
    expect(screen.queryByRole('button', { name: /Xem danh sách \(Các nhóm khác/ })).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Xem danh sách (Chưa gắn)' }))
    await screen.findByText('Lê Thị C')
    expect(lastRowsParams()).toMatchObject({ metric: 'overdue', group_by: 'department', group_key: '' })
    expect(within(screen.getByRole('dialog')).getByText(/Phòng ban: \(Chưa gắn\)/)).toBeInTheDocument()
  })

  it('shows no drilldown action at all when the backend sends no drilldown_metrics', async () => {
    drilldownMetrics = undefined
    renderPage()
    await screen.findAllByText('Đang hiệu lực')
    expect(screen.queryByRole('button', { name: /Xem danh sách/ })).not.toBeInTheDocument()
    expect(screen.queryByText('Danh sách')).not.toBeInTheDocument()
  })

  it('shows no drilldown action when the page has no drilldownEndpoint', async () => {
    renderPage({ ...CONFIG, drilldownEndpoint: undefined })
    await screen.findAllByText('Đang hiệu lực')
    expect(screen.queryByRole('button', { name: /Xem danh sách/ })).not.toBeInTheDocument()
  })
})

describe('ReportAnalyticsPage — hideTrend / hidePeriod', () => {
  it('draws the trend chart by default and switches to the by-group chart with hideTrend', async () => {
    //  duoc-CR-688: biểu đồ linh hoạt — trục thời gian chỉ khi `trend` có mốc; `hideTrend`
    //  (hoặc `trend` rỗng) thì vẽ theo chiều «Xem theo» thay vì bỏ hẳn biểu đồ.
    vi.mocked(apiGet).mockImplementation(async (url) => {
      if (url === ROWS) return ROWS_RESPONSE as never
      const base = summary(drilldownMetrics)
      const point = { key: '2026-10-01', label: '01/10', current: { active: 40 }, compare: null }
      return { ...base, trend: [point] } as never
    })
    const { unmount } = renderPage()
    expect(await screen.findByText('Xu hướng Đang hiệu lực')).toBeInTheDocument()
    unmount()

    renderPage({ ...CONFIG, hideTrend: true })
    await screen.findAllByText('Đang hiệu lực')
    expect(screen.queryByText(/^Xu hướng/)).not.toBeInTheDocument()
    expect(screen.getByText('Đang hiệu lực theo Phòng ban')).toBeInTheDocument()
  })

  it('hides the period control with hidePeriod but still sends the default period', async () => {
    renderPage({ ...CONFIG, hidePeriod: true })
    await screen.findAllByText('Đang hiệu lực')
    expect(screen.queryByRole('button', { name: /Tháng này/ })).not.toBeInTheDocument()
    await waitFor(() => {
      const params = (vi.mocked(apiGet).mock.calls.find(([u]) => u === SUMMARY)?.[1] as {
        params: Record<string, string>
      }).params
      expect(params.preset).toBe('this_month')
    })
  })

  it('keeps the table instead of the «empty period» screen on a hidePeriod report with all zeros', async () => {
    vi.mocked(apiGet).mockImplementation(async () => {
      const base = summary(['overdue'])
      return { ...base, totals: { current: { active: 0, overdue: 0 }, compare: null } } as never
    })
    renderPage({ ...CONFIG, hidePeriod: true })
    await screen.findAllByText('Đang hiệu lực')
    expect(screen.queryByText('Kỳ này chưa có dữ liệu')).not.toBeInTheDocument()
    expect(screen.getAllByRole('row').length).toBeGreaterThan(1)
  })
})
