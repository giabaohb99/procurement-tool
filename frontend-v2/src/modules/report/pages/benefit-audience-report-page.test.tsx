import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { apiGet, downloadFile } from '@/core/api'
import type * as CoreApiModule from '@/core/api'
import { TooltipProvider } from '@/shared/ui/tooltip'

import type { ReportAnalyticsResponse, ReportMetricMeta } from '../types/report-analytics'
import { BenefitAudienceReportPage } from './benefit-audience-report-page'

vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<typeof CoreApiModule>()
  return { ...actual, apiGet: vi.fn(), downloadFile: vi.fn() }
})
//  Có quyền xuất + nhạy cảm; KHÔNG có `department.read`/`company.read` — ô mượn danh mục tự ẩn.
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (entity: string, action: string) =>
      action === 'export' || entity === 'employee_sensitive' || (entity === 'leave_request' && perm.leave),
  }),
}))

const perm = vi.hoisted(() => ({ leave: false }))
const SUMMARY = '/api/benefit-audience/summary'
const SENSITIVE_403 =
  'Bạn chưa có quyền xem ngày sinh và người thân của nhân sự nên không lọc được theo tuổi, tháng sinh hay tuổi con.'

function metric(key: string, label: string, kind: ReportMetricMeta['kind'] = 'int'): ReportMetricMeta {
  return { key, label, kind, good: null, helper: false, snapshot: false }
}

/** Không lọc theo con → backend không trả `children`; thẻ «Số con» phải tự vắng. */
function summary(): ReportAnalyticsResponse {
  const values = { people: 12, managers: 2, staff: 10, budget: 6_400_000 }
  return {
    period: {
      date_from: '2027-03-08', date_to: '2027-03-08', compare_from: null, compare_to: null,
      compare: 'none', granularity: 'day', preset: 'custom',
    },
    meta: {
      metrics: [
        metric('people', 'Số người'), metric('managers', 'Quản lý'),
        metric('staff', 'Nhân viên'), metric('budget', 'Tổng kinh phí', 'money'),
      ],
      dimensions: [{ key: 'company', label: 'Công ty' }, { key: 'department', label: 'Phòng ban' }],
      group_by: 'company',
      drilldown_metrics: ['people'],
    },
    totals: { current: values, compare: null },
    trend: [],
    groups: [{ key: '1', label: 'DEGO Holding', current: values, compare: null }],
  }
}

beforeEach(() => {
  perm.leave = false
  localStorage.clear()
  vi.mocked(apiGet).mockReset().mockImplementation(async () => summary() as never)
  vi.mocked(downloadFile).mockReset().mockResolvedValue(undefined)
})

function renderPage(url = '/report/benefit-audience') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[url]}>
        <TooltipProvider>
          <BenefitAudienceReportPage />
        </TooltipProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const lastSummaryParams = () =>
  (vi.mocked(apiGet).mock.calls.filter(([u]) => u === SUMMARY).at(-1)?.[1] as { params: Record<string, string> })
    .params

describe('BenefitAudienceReportPage (Phúc lợi & sự kiện, khóa 22)', () => {
  it('opens on today grouped by legal entity, without trend chart or the period button', async () => {
    renderPage()
    await screen.findAllByText('Số người')
    expect(lastSummaryParams()).toMatchObject({ preset: 'today', group_by: 'company' })
    expect(screen.queryByText(/^Xu hướng/)).not.toBeInTheDocument()
    //  Ngày dịp nằm trong khung lọc — không có nút «Kỳ báo cáo» thứ hai đặt cùng một thứ.
    //  Nút kỳ ghi chữ preset («Hôm nay …») — vắng hẳn.
    expect(screen.queryByRole('button', { name: /Hôm nay/ })).not.toBeInTheDocument()
    expect(screen.getByLabelText('Ngày dịp')).toBeInTheDocument()
    expect(screen.queryByText('Số con')).not.toBeInTheDocument()
  })

  it('sends a preset occasion to the summary and the sign-off export in the same params', async () => {
    const user = userEvent.setup()
    renderPage('/report/benefit-audience?amount_staff=500000')
    await screen.findAllByText('Số người')
    await user.click(screen.getByRole('button', { name: '8/3' }))
    await waitFor(() => expect(lastSummaryParams()).toMatchObject({ gender: '2', preset: 'custom' }))
    const params = lastSummaryParams()
    expect(params.date_from).toBe(params.date_to)
    expect(params).toMatchObject({ occasion_label: 'Quốc tế Phụ nữ 8/3', amount_staff: '500000', compare: 'none' })

    await user.click(screen.getByRole('button', { name: 'Xuất danh sách ký nhận' }))
    await waitFor(() => expect(downloadFile).toHaveBeenCalledTimes(1))
    expect(downloadFile).toHaveBeenCalledWith(
      '/api/benefit-audience/summary/export',
      expect.stringMatching(/^bao-cao-benefit-audience-.+\.xlsx$/),
      expect.objectContaining({ gender: '2', occasion_label: 'Quốc tế Phụ nữ 8/3', amount_staff: '500000' }),
    )
    expect(screen.queryByRole('button', { name: /Xuất Excel/ })).not.toBeInTheDocument()
  })

  it('shows the plain 403 sentence of a sensitive filter, and the filter panel offers a way out', async () => {
    const err = Object.assign(new Error('403'), {
      response: { status: 403, data: { success: false, error: { code: 'FORBIDDEN', message: SENSITIVE_403 } } },
    })
    vi.mocked(apiGet).mockReset().mockRejectedValue(err)
    const user = userEvent.setup()
    renderPage('/report/benefit-audience?child_max_age=14&occasion_label=Qu%C3%A0+1%2F6')
    expect(await screen.findByText(SENSITIVE_403)).toBeInTheDocument()
    expect(screen.getByText('Không tải được báo cáo')).toBeInTheDocument()

    vi.mocked(apiGet).mockReset().mockImplementation(async () => summary() as never)
    await user.click(screen.getByRole('button', { name: 'Bỏ hết điều kiện' }))
    await screen.findAllByText('Số người')
    expect(lastSummaryParams()).not.toHaveProperty('child_max_age')
  })

  it('drops include_on_leave=0 from the API calls when the viewer cannot read leave requests', async () => {
    renderPage('/report/benefit-audience?include_on_leave=0')
    await screen.findAllByText('Số người')
    expect(lastSummaryParams()).not.toHaveProperty('include_on_leave')
    expect(screen.getByRole('switch', { name: 'Tính người đang nghỉ' })).toBeDisabled()
  })

  it('keeps include_on_leave=0 when the viewer can read leave requests', async () => {
    perm.leave = true
    renderPage('/report/benefit-audience?include_on_leave=0')
    await screen.findAllByText('Số người')
    expect(lastSummaryParams()).toMatchObject({ include_on_leave: '0' })
  })
})
