import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { apiGet, downloadFile } from '@/core/api'
import type * as CoreApiModule from '@/core/api'
import { TooltipProvider } from '@/shared/ui/tooltip'

import type { ReportAnalyticsResponse, ReportMetricMeta } from '../types/report-analytics'
import type { ReportDrilldownResponse } from '../types/report-drilldown'
import { LaborRegisterReportPage } from './labor-register-report-page'

vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<typeof CoreApiModule>()
  return { ...actual, apiGet: vi.fn(), downloadFile: vi.fn() }
})
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: (_entity: string, action: string) => action === 'export' }),
}))

const SUMMARY = '/api/labor-register/summary'
const ROWS = '/api/labor-register/summary/rows'

function metric(key: string, label: string): ReportMetricMeta {
  return { key, label, kind: 'int', good: null, helper: false, snapshot: false }
}

const SUMMARY_RESPONSE: ReportAnalyticsResponse = {
  period: {
    date_from: '2026-01-01', date_to: '2026-12-31', compare_from: null, compare_to: null,
    compare: 'none', granularity: 'month', preset: 'this_year',
  },
  meta: {
    metrics: [
      metric('people', 'Người trong sổ'),
      metric('working', 'Đang làm cuối kỳ'),
      metric('left_in_period', 'Nghỉ việc trong kỳ'),
      metric('missing_required', 'Thiếu thông tin bắt buộc'),
    ],
    dimensions: [{ key: 'department', label: 'Phòng ban' }],
    group_by: 'department',
    drilldown_metrics: ['people', 'missing_required'],
  },
  totals: { current: { people: 12, working: 10, left_in_period: 2, missing_required: 3 }, compare: null },
  trend: [],
  groups: [
    { key: '5', label: 'Kế toán', current: { people: 12, working: 10, left_in_period: 2, missing_required: 3 }, compare: null },
  ],
  notes: [],
}

const ROWS_RESPONSE: ReportDrilldownResponse = {
  metric: { key: 'missing_required', label: 'Thiếu thông tin bắt buộc' },
  columns: [{ key: 'employee_name', label: 'Họ tên', kind: 'text' }],
  rows: [{ employee_name: 'Trần Văn D' }],
  total: 1,
  truncated: false,
}

beforeEach(() => {
  localStorage.clear()
  vi.mocked(apiGet).mockReset().mockImplementation(async (url) =>
    (url === ROWS ? ROWS_RESPONSE : SUMMARY_RESPONSE) as never,
  )
  vi.mocked(downloadFile).mockReset().mockResolvedValue(undefined)
})

function renderPage(url = '/report/labor-register') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[url]}>
        <TooltipProvider>
          <LaborRegisterReportPage />
        </TooltipProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const callParams = (endpoint: string) =>
  (vi.mocked(apiGet).mock.calls.filter(([u]) => u === endpoint).at(-1)?.[1] as {
    params: Record<string, string>
  }).params

describe('LaborRegisterReportPage (sổ quản lý lao động, khóa 19)', () => {
  it('opens on this year grouped by department, without a trend chart', async () => {
    renderPage()
    await screen.findAllByText('Người trong sổ')
    expect(callParams(SUMMARY)).toMatchObject({ preset: 'this_year', group_by: 'department' })
    expect(screen.queryByText(/^Xu hướng/)).not.toBeInTheDocument()
  })

  it('opens the people missing required data from the KPI card, keeping the URL department filter', async () => {
    const user = userEvent.setup()
    renderPage('/report/labor-register?department_id=5')
    await user.click(await screen.findByRole('button', { name: 'Xem danh sách Thiếu thông tin bắt buộc' }))
    expect(await screen.findByText('Trần Văn D')).toBeInTheDocument()
    expect(callParams(ROWS)).toMatchObject({ metric: 'missing_required', group_by: 'none', department_id: '5' })
  })

  it('labels the export «Xuất sổ (Excel)» and downloads the register file', async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findAllByText('Người trong sổ')
    await user.click(screen.getByRole('button', { name: 'Xuất sổ (Excel)' }))
    await waitFor(() => expect(downloadFile).toHaveBeenCalledTimes(1))
    expect(downloadFile).toHaveBeenCalledWith(
      '/api/labor-register/summary/export',
      expect.stringMatching(/^bao-cao-labor-register-.*\.xlsx$/),
      expect.objectContaining({ preset: 'this_year' }),
    )
  })
})
