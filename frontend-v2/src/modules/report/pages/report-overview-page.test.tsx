import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { apiGet } from '@/core/api'

import type { ReportAnalyticsResponse, ReportMetricMeta } from '../types/report-analytics'
import { ReportOverviewPage } from './report-overview-page'

//  Cùng lối mock của `report-analytics-page.test.tsx`: biên mạng giả ở tầng
//  `@/core/api`, `can()` điều khiển được TỪNG entity để giả lập thiếu quyền.
vi.mock('@/core/api', () => ({ apiGet: vi.fn(), downloadFile: vi.fn() }))

let readableEntities: string[] = []
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (entity: string, action: string) => action === 'read' && readableEntities.includes(entity),
  }),
}))

function metric(
  overrides: Partial<ReportMetricMeta> & Pick<ReportMetricMeta, 'key' | 'label' | 'kind'>,
): ReportMetricMeta {
  return { good: null, helper: false, snapshot: false, ...overrides }
}

function buildFixture(
  metrics: ReportMetricMeta[],
  breakdownKeys: string[] = [],
): ReportAnalyticsResponse {
  const current: Record<string, number> = {}
  const compare: Record<string, number> = {}
  metrics.forEach((m, i) => {
    current[m.key] = (i + 1) * 10
    compare[m.key] = i + 1
  })
  return {
    period: {
      date_from: '2026-09-01',
      date_to: '2026-09-28',
      compare_from: '2026-08-01',
      compare_to: '2026-08-28',
      compare: 'previous',
      granularity: 'day',
      preset: 'this_month',
    },
    meta: { metrics, dimensions: [], group_by: 'none' },
    totals: { current, compare },
    trend: [],
    breakdowns: Object.fromEntries(
      breakdownKeys.map((key) => [key, [{ key: 'x', label: 'X', value: 5 }]]),
    ),
    notes: [],
  }
}

/** `procurementBreakdowns` mô phỏng đúng những gì `_can_see_ncc` quyết định ở backend. */
function mockOverviewApi(procurementBreakdowns: string[]) {
  vi.mocked(apiGet).mockImplementation(async (url: unknown) => {
    switch (url) {
      case '/api/reports/procurement/summary':
        return buildFixture(
          [
            metric({ key: 'spend', label: 'Chi phí mua hàng', kind: 'money' }),
            metric({ key: 'on_time_rate', label: 'Giao đúng hạn', kind: 'percent', good: 'up' }),
          ],
          procurementBreakdowns,
        )
      case '/api/reports/pr-lines/summary':
        return buildFixture([
          metric({ key: 'idle_lines', label: 'Dòng chưa đặt', kind: 'int', good: 'down' }),
        ])
      case '/api/survey-progress/summary':
        return buildFixture([metric({ key: 'late', label: 'Trễ hạn', kind: 'int', good: 'down' })])
      case '/api/purchase-progress/summary':
        return buildFixture([
          metric({ key: 'on_time_rate', label: 'Giao đúng hạn', kind: 'percent', good: 'up' }),
        ])
      case '/api/survey-report/summary':
        return buildFixture([
          metric({ key: 'approved_rate', label: 'Tỷ lệ duyệt', kind: 'percent', good: 'up' }),
        ])
      default:
        throw new Error(`report-overview-page.test.tsx: endpoint không mong đợi — ${String(url)}`)
    }
  })
}

beforeEach(() => {
  readableEntities = []
  vi.mocked(apiGet).mockReset()
})

function renderOverview(url = '/report') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[url]}>
        <ReportOverviewPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ReportOverviewPage — KPI strip hides blocks without read permission', () => {
  it('only fetches and renders reports the user can read, even when two reports share an entity', async () => {
    //  `report` gác CẢ Báo cáo mua hàng LẪN Chi tiết YC mua hàng (cùng entity) —
    //  test này canh đúng việc đó, không phải một sự trùng hợp cần "sửa".
    readableEntities = ['report']
    mockOverviewApi(['department', 'item_group'])
    renderOverview()

    await screen.findByText('Chi phí mua hàng')
    expect(screen.getByText('Dòng chưa đặt')).toBeInTheDocument()
    //  "Giao đúng hạn" là nhãn CHUNG của on_time_rate ở cả Báo cáo mua hàng
    //  (entity `report`, được phép) LẪN Tiến độ mua hàng (entity
    //  `purchase_request`, KHÔNG được phép) — phải chỉ còn đúng một thẻ.
    expect(screen.getAllByText('Giao đúng hạn')).toHaveLength(1)
    expect(screen.queryByText('Trễ hạn')).not.toBeInTheDocument()
    expect(screen.queryByText('Tỷ lệ duyệt')).not.toBeInTheDocument()

    const calledEndpoints = vi.mocked(apiGet).mock.calls.map((call) => call[0])
    expect(calledEndpoints).not.toContain('/api/survey-progress/summary')
    expect(calledEndpoints).not.toContain('/api/purchase-progress/summary')
    expect(calledEndpoints).not.toContain('/api/survey-report/summary')
  })

  it('renders nothing from the KPI strip / top lists when no report entity is readable', async () => {
    readableEntities = []
    mockOverviewApi([])
    renderOverview()

    //  Không có gì để tải — chờ một nhịp render rồi khẳng định KHÔNG có gọi API nào.
    await screen.findByRole('heading', { name: 'Báo cáo' })
    expect(apiGet).not.toHaveBeenCalled()
    expect(screen.queryByText('Chi phí mua hàng')).not.toBeInTheDocument()
  })
})

describe('ReportOverviewPage — top lists follow what the procurement summary actually returns', () => {
  it('hides Top NCC / Top NSPT when the backend omits them (no purchase_order.read)', async () => {
    readableEntities = ['report']
    mockOverviewApi(['department', 'item_group'])
    renderOverview()

    await screen.findByText('Chi phí mua hàng')
    expect(await screen.findByText('Top bộ phận')).toBeInTheDocument()
    expect(screen.getByText('Top nhóm hàng')).toBeInTheDocument()
    expect(screen.queryByText('Top NCC')).not.toBeInTheDocument()
    expect(screen.queryByText('Top NSPT')).not.toBeInTheDocument()
  })

  it('shows Top NCC / Top NSPT once the backend includes them', async () => {
    readableEntities = ['report']
    mockOverviewApi(['department', 'item_group', 'supplier', 'nspt'])
    renderOverview()

    await screen.findByText('Chi phí mua hàng')
    expect(await screen.findByText('Top NCC')).toBeInTheDocument()
    expect(screen.getByText('Top NSPT')).toBeInTheDocument()
  })
})

//  item 4 — thiếu `report.read` thì KHÔNG được hiện thẻ Top rỗng, kể cả khi
// một báo cáo KHÁC (entity riêng) vẫn đọc được và dải KPI vẫn hiện.
describe('ReportOverviewPage — Top lists hidden entirely without report.read, even if another entity is readable', () => {
  it('renders the KPI strip for the readable report but no Top-list card at all', async () => {
    readableEntities = ['survey_request']
    mockOverviewApi([])
    renderOverview()

    await screen.findByText('Trễ hạn')
    expect(screen.queryByText('Top bộ phận')).not.toBeInTheDocument()
    expect(screen.queryByText('Top nhóm hàng')).not.toBeInTheDocument()
    expect(screen.queryByText('Top NCC')).not.toBeInTheDocument()
    //  Endpoint của Báo cáo mua hàng không được gọi — người dùng không có quyền.
    const calledEndpoints = vi.mocked(apiGet).mock.calls.map((call) => call[0])
    expect(calledEndpoints).not.toContain('/api/reports/procurement/summary')
  })
})

//  item 4 — nguồn `hideCompany` (Báo cáo khảo sát) không được nhận `company_id`
//  dù người dùng đang lọc theo công ty ở trang Tổng quan (L7).
describe('ReportOverviewPage — hideCompany reports never receive company_id', () => {
  it('sends company_id to the procurement summary but strips it for survey-report', async () => {
    readableEntities = ['report', 'survey']
    mockOverviewApi([])
    renderOverview('/report?company_id=7')

    await screen.findByText('Chi phí mua hàng')

    const purchaseCall = vi
      .mocked(apiGet)
      .mock.calls.find((call) => call[0] === '/api/reports/procurement/summary')
    const surveyCall = vi
      .mocked(apiGet)
      .mock.calls.find((call) => call[0] === '/api/survey-report/summary')

    expect((purchaseCall?.[1] as { params?: Record<string, string> })?.params?.company_id).toBe('7')
    expect((surveyCall?.[1] as { params?: Record<string, string> })?.params).not.toHaveProperty(
      'company_id',
    )
  })
})
