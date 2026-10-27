import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, within } from '@testing-library/react'
import { cloneElement, isValidElement, type ReactElement, type ReactNode } from 'react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { apiGet } from '@/core/api'
import type * as CoreApiModule from '@/core/api'
import { TooltipProvider } from '@/shared/ui/tooltip'
import type * as RechartsModule from 'recharts'

import { ReportAnalyticsPage } from '../pages/report-analytics-page'
import type { ReportAnalyticsResponse, ReportPageConfig } from '../types/report-analytics'

/**
 * Bấm cột của biểu đồ linh hoạt trên TRANG THẬT (duoc-CR-688): đi hết đường biểu đồ →
 * `ReportAnalyticsBody` → `useReportDrilldownState.openRow` → ngăn «Danh sách» → `/summary/rows`.
 * Chỉ giả biên mạng (`@/core/api`) và khung đo của recharts (jsdom đo ra 0×0).
 */
vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<typeof CoreApiModule>()
  return { ...actual, apiGet: vi.fn(), downloadFile: vi.fn() }
})
vi.mock('@/core/authorization/use-permission', () => ({ usePermission: () => ({ can: () => false }) }))
vi.mock('recharts', async (importOriginal) => {
  const actual = await importOriginal<typeof RechartsModule>()
  return {
    ...actual,
    ResponsiveContainer: ({ children }: { children: ReactNode }) =>
      isValidElement(children)
        ? cloneElement(children as ReactElement<{ width: number; height: number }>, {
            width: 600,
            height: 400,
          })
        : null,
  }
})

const SUMMARY = '/api/labor-contracts/summary'
const ROWS = '/api/labor-contracts/summary/rows'

let drilldownMetrics: string[] = []
function summary(): ReportAnalyticsResponse {
  return {
    period: {
      date_from: '2026-10-01', date_to: '2026-10-27', compare_from: null, compare_to: null,
      compare: 'none', granularity: 'day', preset: 'this_month',
    },
    meta: {
      metrics: [
        { key: 'active', label: 'Đang hiệu lực', kind: 'int', good: null, helper: false, snapshot: false },
      ],
      dimensions: [{ key: 'department', label: 'Phòng ban' }],
      group_by: 'department',
      drilldown_metrics: drilldownMetrics,
    },
    totals: { current: { active: 40 }, compare: null },
    trend: [],
    groups: [
      { key: '5', label: 'Kế toán', current: { active: 30 }, compare: null },
      { key: '', label: '(Chưa gắn)', current: { active: 8 }, compare: null },
    ],
    notes: [],
  }
}

const CONFIG: ReportPageConfig = {
  endpoint: SUMMARY,
  drilldownEndpoint: ROWS,
  entity: 'labor_contract',
  title: 'Hợp đồng lao động',
  description: 'Mô tả.',
  slug: 'labor-contract-test',
  kpis: ['active'],
  chartMetric: 'active',
  defaultGroupBy: 'department',
  hideTrend: true,
}

beforeEach(() => {
  localStorage.clear()
  drilldownMetrics = ['active']
  vi.mocked(apiGet).mockReset()
  vi.mocked(apiGet).mockImplementation(async (url) =>
    (url === ROWS
      ? {
          metric: { key: 'active', label: 'Đang hiệu lực' },
          columns: [{ key: 'employee_name', label: 'Họ tên', kind: 'text' }],
          rows: [{ employee_name: 'Lê Thị C' }],
          total: 1,
          truncated: false,
        }
      : summary()) as never,
  )
})

function renderPage(url = '/report/labor-contract') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[url]}>
        <TooltipProvider>
          <ReportAnalyticsPage config={CONFIG} />
        </TooltipProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const rowsParams = () =>
  vi.mocked(apiGet).mock.calls.filter(([u]) => u === ROWS).map(([, c]) => (c as { params: Record<string, string> }).params)

function clickBar(container: HTMLElement, index: number) {
  const bar = container.querySelectorAll('.recharts-bar-rectangle')[index]
  const target = bar?.querySelector('path') ?? bar
  if (!target) throw new Error(`no bar #${index}`)
  fireEvent.click(target)
}

describe('ReportAnalyticsPage — flexible chart click opens the group list', () => {
  it('sends the chart metric and the clicked group key, "" included for «(Chưa gắn)»', async () => {
    const { container } = renderPage()
    expect(await screen.findByText('Đang hiệu lực theo Phòng ban')).toBeInTheDocument()
    clickBar(container, 1)
    expect(await screen.findByText('Lê Thị C')).toBeInTheDocument()
    expect(rowsParams().at(-1)).toMatchObject({ metric: 'active', group_by: 'department', group_key: '' })
    expect(within(screen.getByRole('dialog')).getByText(/Phòng ban: \(Chưa gắn\)/)).toBeInTheDocument()
  })

  it('does not open anything when the chart metric has no list', async () => {
    drilldownMetrics = []
    const { container } = renderPage()
    await screen.findByText('Đang hiệu lực theo Phòng ban')
    clickBar(container, 0)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(rowsParams()).toHaveLength(0)
  })

  it('keeps the chart params out of the /summary request', async () => {
    renderPage('/report/labor-contract?chart_type=bar')
    await screen.findByText('Đang hiệu lực theo Phòng ban')
    const summaryCalls = vi.mocked(apiGet).mock.calls.filter(([u]) => u === SUMMARY)
    expect(summaryCalls).toHaveLength(1)
    expect((summaryCalls[0]?.[1] as { params: Record<string, string> }).params).not.toHaveProperty(
      'chart_type',
    )
  })
})

describe('ReportAnalyticsPage — snapshot metric carried by groups', () => {
  it('lets the snapshot KPI be picked and draws it by group, even in a period with no movement', async () => {
    //  Biến động nhân sự tháng không ai vào/nghỉ: chỉ số theo kỳ toàn 0, nhưng «Định biên cuối
    //  kỳ» (thời điểm) vẫn có ở từng phòng — không được thay cả khối bằng «Kỳ này chưa có dữ liệu».
    vi.mocked(apiGet).mockImplementation(async () => {
      const base = summary()
      return {
        ...base,
        meta: {
          ...base.meta,
          metrics: [
            { key: 'new_hires', label: 'Vào mới', kind: 'int', good: null, helper: false, snapshot: false },
            { key: 'headcount_end', label: 'Định biên cuối kỳ', kind: 'int', good: null, helper: false, snapshot: true },
          ],
        },
        totals: { current: { new_hires: 0, headcount_end: 12 }, compare: null },
        groups: [
          { key: '1', label: 'Kế toán', current: { new_hires: 0, headcount_end: 7 }, compare: null },
          { key: '2', label: 'Kinh doanh', current: { new_hires: 0, headcount_end: 5 }, compare: null },
        ],
      } as never
    })
    const config = { ...CONFIG, hideTrend: false, kpis: ['headcount_end', 'new_hires'], chartMetric: 'new_hires' }
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={['/report/hr-headcount']}>
          <TooltipProvider>
            <ReportAnalyticsPage config={config} />
          </TooltipProvider>
        </MemoryRouter>
      </QueryClientProvider>,
    )
    const card = await screen.findByRole('button', { name: /Định biên cuối kỳ/ })
    expect(screen.queryByText('Kỳ này chưa có dữ liệu')).not.toBeInTheDocument()
    fireEvent.click(card)
    expect(await screen.findByText('Định biên cuối kỳ theo Phòng ban')).toBeInTheDocument()
  })
})
