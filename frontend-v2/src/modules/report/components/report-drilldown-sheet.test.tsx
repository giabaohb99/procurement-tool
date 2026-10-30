import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ComponentProps } from 'react'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { apiGet } from '@/core/api'
import type * as CoreApiModule from '@/core/api'
import { TooltipProvider } from '@/shared/ui/tooltip'

import type { ReportDrilldownResponse } from '../types/report-drilldown'
import { ReportDrilldownSheet } from './report-drilldown-sheet'

vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<typeof CoreApiModule>()
  return { ...actual, apiGet: vi.fn() }
})

const ENDPOINT = '/api/labor-contracts/summary/rows'
const OPTIONS = [
  { key: 'expiring_30', label: 'Hết hạn trong 30 ngày' },
  { key: 'overdue', label: 'Đã quá hạn, vẫn đi làm' },
]

function response(overrides: Partial<ReportDrilldownResponse> = {}): ReportDrilldownResponse {
  return {
    metric: { key: 'expiring_30', label: 'Hết hạn trong 30 ngày' },
    columns: [
      { key: 'employee_code', label: 'Mã NV', kind: 'text' },
      { key: 'employee_name', label: 'Họ tên', kind: 'text' },
      { key: 'end_date', label: 'Kết thúc', kind: 'date' },
      { key: 'days_left', label: 'Còn (ngày)', kind: 'days' },
      { key: 'base_salary', label: 'Lương cơ bản', kind: 'money' },
    ],
    rows: [
      {
        employee_code: 'NSU001',
        employee_name: 'Nguyễn Văn A',
        end_date: '2026-11-15',
        days_left: 19,
        base_salary: '15000000.00',
        link: '/hr/employees/12?tab=labor-contracts',
      },
      //  Dòng có `link` ra ngoài — bấm không được đi đâu cả.
      { employee_code: 'NSU002', employee_name: 'Trần B', end_date: null, days_left: 0, link: 'https://evil.example' },
    ],
    total: 2,
    truncated: false,
    ...overrides,
  }
}

function LocationProbe() {
  const location = useLocation()
  return <p data-testid="location">{location.pathname + location.search}</p>
}

function renderSheet(props: Partial<ComponentProps<typeof ReportDrilldownSheet>> = {}) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const onMetricChange = vi.fn()
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={['/report/labor-contract']}>
        <TooltipProvider>
          <Routes>
            <Route
              path="*"
              element={
                <>
                  <LocationProbe />
                  <ReportDrilldownSheet
                    endpoint={ENDPOINT}
                    baseParams={{ preset: 'this_month', group_by: 'department', department_id: '7' }}
                    target={{ metric: 'expiring_30', group: null }}
                    metricOptions={OPTIONS}
                    onMetricChange={onMetricChange}
                    onClose={vi.fn()}
                    storageKey="report.test"
                    {...props}
                  />
                </>
              }
            />
          </Routes>
        </TooltipProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  )
  return { onMetricChange }
}

function lastParams(): Record<string, string> {
  const call = vi.mocked(apiGet).mock.calls.at(-1)
  return (call?.[1] as { params: Record<string, string> }).params
}

beforeEach(() => {
  localStorage.clear()
  vi.mocked(apiGet).mockReset()
  vi.mocked(apiGet).mockResolvedValue(response())
})

describe('ReportDrilldownSheet', () => {
  it('does not call the rows endpoint while closed', () => {
    renderSheet({ target: null })
    expect(apiGet).not.toHaveBeenCalled()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('asks for the whole list with every page filter when opened from a KPI card', async () => {
    renderSheet()
    expect(await screen.findByText('Nguyễn Văn A')).toBeInTheDocument()
    expect(vi.mocked(apiGet).mock.calls.at(-1)?.[0]).toBe(ENDPOINT)
    expect(lastParams()).toEqual({
      preset: 'this_month',
      department_id: '7',
      metric: 'expiring_30',
      group_by: 'none',
    })
    expect(screen.getByText('Toàn bộ báo cáo · cùng bộ lọc đang xem trên trang.')).toBeInTheDocument()
  })

  it('sends the empty "(Chưa gắn)" group key and names the group in the subtitle', async () => {
    renderSheet({
      target: {
        metric: 'overdue',
        group: { by: 'department', key: '', dimensionLabel: 'Phòng ban', label: '(Chưa gắn)' },
      },
    })
    await screen.findByText('Nguyễn Văn A')
    expect(lastParams()).toMatchObject({ metric: 'overdue', group_by: 'department', group_key: '' })
    expect(screen.getByText(/Phòng ban: \(Chưa gắn\)/)).toBeInTheDocument()
  })

  it('renders backend columns with formatting by kind and keeps a real zero', async () => {
    renderSheet()
    await screen.findByText('Nguyễn Văn A')
    for (const header of ['Mã NV', 'Họ tên', 'Kết thúc', 'Còn (ngày)', 'Lương cơ bản']) {
      expect(screen.getAllByText(header).length).toBeGreaterThan(0)
    }
    expect(screen.getByText('15/11/2026')).toBeInTheDocument()
    expect(screen.getByText('19 ngày')).toBeInTheDocument()
    expect(screen.getByText('0 ngày')).toBeInTheDocument()
    expect(screen.getByText('15.000.000 đ')).toBeInTheDocument()
    expect(screen.getByText('2 dòng')).toBeInTheDocument()
  })

  it('opens the internal link of a row, and ignores an external one', async () => {
    const user = userEvent.setup()
    renderSheet()
    await user.click(await screen.findByText('Trần B'))
    expect(screen.getByTestId('location')).toHaveTextContent('/report/labor-contract')
    await user.click(screen.getByText('Nguyễn Văn A'))
    await waitFor(() =>
      expect(screen.getByTestId('location')).toHaveTextContent('/hr/employees/12?tab=labor-contracts'),
    )
  })

  it('warns that only the first rows are shown when the backend truncated the list', async () => {
    vi.mocked(apiGet).mockResolvedValue(response({ total: 1234, truncated: true }))
    renderSheet()
    expect(await screen.findByText(/Chỉ hiện 2 dòng đầu trên tổng 1.234\./)).toBeInTheDocument()
  })

  it('says the list is empty instead of showing an empty grid silently', async () => {
    vi.mocked(apiGet).mockResolvedValue(response({ rows: [], total: 0 }))
    renderSheet()
    expect(await screen.findByText(/^Không có ai theo chỉ số ".+" — đổi chỉ số ở ô phía trên\.$/)).toBeInTheDocument()
  })

  it('shows the backend error and retries on demand', async () => {
    const err = Object.assign(new Error('422'), {
      response: { status: 422, data: { success: false, error: { message: 'Chỉ số không có danh sách: x' } } },
    })
    vi.mocked(apiGet).mockRejectedValue(err)
    const user = userEvent.setup()
    renderSheet()
    expect(await screen.findByText('Chỉ số không có danh sách: x')).toBeInTheDocument()
    const calls = vi.mocked(apiGet).mock.calls.length
    await user.click(screen.getByRole('button', { name: 'Thử lại' }))
    await waitFor(() => expect(vi.mocked(apiGet).mock.calls.length).toBe(calls + 1))
  })

  it('offers only drilldown metrics in the selector and reports the choice', async () => {
    const user = userEvent.setup()
    const { onMetricChange } = renderSheet()
    await screen.findByText('Nguyễn Văn A')
    await user.click(screen.getByRole('combobox', { name: 'Chỉ số' }))
    const options = screen.getAllByRole('option').map((o) => o.textContent)
    expect(options).toEqual(['Hết hạn trong 30 ngày', 'Đã quá hạn, vẫn đi làm'])
    await user.click(screen.getByRole('option', { name: 'Đã quá hạn, vẫn đi làm' }))
    expect(onMetricChange).toHaveBeenCalledWith('overdue')
  })
})
