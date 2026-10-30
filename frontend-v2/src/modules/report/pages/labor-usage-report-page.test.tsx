import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { apiGet, downloadFile } from '@/core/api'
import type * as CoreApiModule from '@/core/api'
import { TooltipProvider } from '@/shared/ui/tooltip'

import type { ReportAnalyticsResponse, ReportMetricMeta } from '../types/report-analytics'
import { LaborUsageReportPage } from './labor-usage-report-page'

vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<typeof CoreApiModule>()
  return { ...actual, apiGet: vi.fn(), downloadFile: vi.fn() }
})
//  Có quyền xuất; KHÔNG có `department.read`/`company.read` — ô lọc mượn danh mục tự ẩn.
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: (_entity: string, action: string) => action === 'export' }),
}))

const SUMMARY = '/api/labor-usage-report/summary'

function metric(key: string, label: string): ReportMetricMeta {
  return { key, label, kind: 'int', good: null, helper: false, snapshot: false }
}

/** Đúng 9 chỉ số phase 07 §B3, nhãn như backend khai. */
const METRICS = [
  metric('people', 'Tổng lao động'),
  metric('female', 'Nữ'),
  metric('job_manager', 'Nhà quản lý'),
  metric('job_high', 'Chuyên môn kỹ thuật bậc cao'),
  metric('job_mid', 'Chuyên môn kỹ thuật bậc trung'),
  metric('job_other', 'Vị trí việc làm khác'),
  metric('ct_indefinite', 'HĐ không xác định thời hạn'),
  metric('ct_fixed', 'HĐ xác định thời hạn'),
  metric('ct_other', 'HĐ khác (thử việc, chưa có HĐ)'),
]

function summary(): ReportAnalyticsResponse {
  const values = {
    people: 10, female: 4, job_manager: 1, job_high: 3, job_mid: 4, job_other: 2,
    ct_indefinite: 5, ct_fixed: 3, ct_other: 2,
  }
  return {
    period: {
      date_from: '2026-01-01', date_to: '2026-12-31', compare_from: null, compare_to: null,
      compare: 'none', granularity: 'month', preset: 'this_year',
    },
    meta: {
      metrics: METRICS,
      dimensions: [{ key: 'company', label: 'Công ty' }, { key: 'department', label: 'Phòng ban' }],
      group_by: 'company',
      drilldown_metrics: ['people'],
    },
    totals: { current: values, compare: null },
    trend: [],
    groups: [{ key: '1', label: 'DEGO Holding', current: values, compare: null }],
    notes: ['Cột 13–15, 17–19, 25–26 để trống trong tệp — Nhân sự điền tay.'],
  }
}

beforeEach(() => {
  localStorage.clear()
  vi.mocked(apiGet).mockReset().mockImplementation(async () => summary() as never)
  vi.mocked(downloadFile).mockReset().mockResolvedValue(undefined)
})

function renderPage(url = '/report/labor-usage-report') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[url]}>
        <TooltipProvider>
          <LaborUsageReportPage />
        </TooltipProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const summaryParams = () =>
  (vi.mocked(apiGet).mock.calls.find(([u]) => u === SUMMARY)?.[1] as { params: Record<string, string> })
    .params

describe('LaborUsageReportPage (mẫu 01/PLI, khóa 20)', () => {
  it('opens on this year, grouped by legal entity, with no trend chart', async () => {
    renderPage()
    await screen.findAllByText('Tổng lao động')
    expect(summaryParams()).toMatchObject({ preset: 'this_year', group_by: 'company' })
    expect(screen.queryByText(/^Xu hướng/)).not.toBeInTheDocument()
  })

  it('shows the four KPI cards and every composition metric as a visible table column', async () => {
    renderPage()
    await screen.findAllByText('Tổng lao động')
    const headers = (await screen.findAllByRole('columnheader')).map((h) => h.textContent)
    expect(headers).toEqual([
      'Công ty',
      'Tổng lao động', 'Nữ', 'Nhà quản lý', 'Chuyên môn kỹ thuật bậc cao',
      'Chuyên môn kỹ thuật bậc trung', 'Vị trí việc làm khác',
      'HĐ không xác định thời hạn', 'HĐ xác định thời hạn', 'HĐ khác (thử việc, chưa có HĐ)',
      'Danh sách',
    ])
  })

  it('tells HR when to file and that blank columns must be filled by hand', async () => {
    renderPage()
    expect(await screen.findByText(/Nộp Sở Nội vụ trước 05\/6 và 05\/12/)).toBeInTheDocument()
    expect(screen.getByText(/điền tay trước khi nộp/)).toBeInTheDocument()
  })

  it('labels the export "Xuất mẫu 01/PLI" and downloads from the form endpoint', async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findAllByText('Tổng lao động')
    expect(screen.queryByRole('button', { name: /Xuất Excel/ })).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Xuất mẫu 01/PLI' }))
    await waitFor(() => expect(downloadFile).toHaveBeenCalledTimes(1))
    expect(downloadFile).toHaveBeenCalledWith(
      '/api/labor-usage-report/summary/export',
      expect.stringMatching(/^bao-cao-labor-usage-report-2026-01-01-2026-12-31\.xlsx$/),
      expect.objectContaining({ preset: 'this_year', group_by: 'company' }),
    )
  })
})
