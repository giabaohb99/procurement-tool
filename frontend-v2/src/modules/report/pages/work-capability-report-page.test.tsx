import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { apiGet } from '@/core/api'

import type { CapabilityStats, CapabilitySummary } from '../types/work-capability'
import { WorkCapabilityReportPage } from './work-capability-report-page'

vi.mock('@/core/api', () => ({ apiGet: vi.fn(), downloadFile: vi.fn(), extractErrorMessage: () => 'lỗi' }))
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => false }),
  useNavContext: () => ({}),
}))
vi.mock('@/modules/hr/hooks/use-departments', () => ({ useDepartments: () => ({ data: { items: [] } }) }))
vi.mock('@/modules/hr/hooks/use-companies', () => ({ useCompanies: () => ({ data: { items: [] } }) }))
vi.mock('@/modules/work/hooks/use-task-types', () => ({ useActiveTaskTypes: () => ({ data: [] }) }))

const enough: CapabilityStats = {
  n_done: 12, n_estimated: 3, below_threshold: false, mean_days: 4, p50_days: 3.5, p90_days: 8, max_days: 9,
  rework_rate: 0.08, first_pass_rate: 0.9, late_rate: null, est_ratio_p50: null,
}
const few: CapabilityStats = {
  n_done: 2, n_estimated: 0, below_threshold: true, mean_days: null, p50_days: null, p90_days: null, max_days: null,
  rework_rate: null, first_pass_rate: null, late_rate: null, est_ratio_p50: null,
}
const typeBase = { kind: 1, kind_label: 'Yêu cầu mua hàng', task_type_id: 0, task_type_name: '' }
const summary: CapabilitySummary = {
  period: { date_from: '2026-09-21', date_to: '2026-10-20' },
  types: [{ ...typeBase, ...enough }],
  people: [
    { ...typeBase, ...enough, employee_id: 1, employee_code: 'A', full_name: 'Chị A', department_id: 1 },
    { ...typeBase, ...few, employee_id: 2, employee_code: 'B', full_name: 'Anh B', department_id: 1 },
  ],
  n_estimated: 3, min_samples: 5, truncated: false,
}

function renderPage(url = '/report/work-capability') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[url]}>
        <WorkCapabilityReportPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => vi.mocked(apiGet).mockReset())

describe('WorkCapabilityReportPage (duoc-CR-657)', () => {
  it('shows the reference-only notice and the type table with p50 / estimated count', async () => {
    vi.mocked(apiGet).mockResolvedValue(summary)
    renderPage()
    expect(screen.getByRole('note')).toHaveTextContent(/không dùng để chấm điểm/)
    expect(screen.getByRole('note')).toHaveTextContent(/việc khó/)
    expect((await screen.findAllByText('Yêu cầu mua hàng')).length).toBeGreaterThan(0)
    expect(screen.getAllByText('3,5 ngày').length).toBeGreaterThan(0)
    expect(screen.getAllByText(/\+3 ước tính/).length).toBeGreaterThan(0)
  })

  it('shows "chưa đủ mẫu" instead of numbers for a person below the threshold', async () => {
    vi.mocked(apiGet).mockResolvedValue(summary)
    renderPage()
    await userEvent.click(await screen.findByRole('tab', { name: 'Theo người' }))
    expect(await screen.findByText('Anh B (B)')).toBeInTheDocument()
    expect(screen.getByText('(chưa đủ mẫu)')).toBeInTheDocument()
  })

  it('asks for a scope on the load tab and does not call /load without one', async () => {
    vi.mocked(apiGet).mockResolvedValue(summary)
    renderPage()
    await userEvent.click(await screen.findByRole('tab', { name: 'Tải đang ôm' }))
    expect(await screen.findByText(/Chọn một pháp nhân hoặc một phòng ban/)).toBeInTheDocument()
    expect(vi.mocked(apiGet).mock.calls.some(([url]) => String(url).endsWith('/load'))).toBe(false)
  })

  it('calls /load once a department is chosen', async () => {
    vi.mocked(apiGet).mockImplementation(async (url?: string) =>
      String(url).endsWith('/load') ? { items: [], count: 0, horizon_days: 14 } : summary,
    )
    renderPage('/report/work-capability?department_id=7')
    await userEvent.click(await screen.findByRole('tab', { name: 'Tải đang ôm' }))
    await screen.findByText(/Không có nhân sự nào/)
    const call = vi.mocked(apiGet).mock.calls.find(([url]) => String(url).endsWith('/load'))
    expect(call?.[1]).toMatchObject({ params: { department_id: '7' } })
  })

  //  Lỗi 22/10/2026: không loại nào đủ mẫu thì cả khung biểu đồ biến mất, không một chữ giải thích.
  it('keeps the chart card and explains when no type reaches the sample threshold', async () => {
    vi.mocked(apiGet).mockResolvedValue({ ...summary, types: [{ ...typeBase, ...few }] })
    renderPage()
    expect(await screen.findByText('Thời gian trọn vòng — trung vị (ngày)')).toBeInTheDocument()
    expect(screen.getByText(/Chưa loại việc nào đủ 5 phiếu xong trong kỳ/)).toBeInTheDocument()
  })

  it('keeps the chart card and suggests a longer period when nothing finished', async () => {
    vi.mocked(apiGet).mockResolvedValue({ ...summary, types: [], people: [] })
    renderPage()
    expect(await screen.findByText('Thời gian trọn vòng — trung vị (ngày)')).toBeInTheDocument()
    expect(screen.getByText(/chọn kỳ dài hơn để xem biểu đồ/)).toBeInTheDocument()
  })
})
