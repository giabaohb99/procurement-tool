import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { apiGet } from '@/core/api'

import type { UsageProfileListResponse } from '../types/usage-profile'
import { UsageProfileListPage } from './usage-profile-list-page'

vi.mock('@/core/api', () => ({ apiGet: vi.fn(), downloadFile: vi.fn(), extractErrorMessage: () => 'lỗi' }))
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => false }),
  useNavContext: () => ({}),
}))
vi.mock('@/modules/hr/hooks/use-roles', () => ({ useRoles: () => ({ data: [] }) }))
vi.mock('@/modules/hr/hooks/use-departments', () => ({ useDepartments: () => ({ data: { items: [] } }) }))

const response: UsageProfileListResponse = {
  items: [
    {
      user_id: 7,
      full_name: 'Trần Thị B',
      emp_code: 'NV007',
      department_name: 'Thu mua',
      cohort: { kind: 1, key: 4, size: 6, name: 'Thu mua' },
      active_days: 18,
      workdays_net: 20,
      active_ratio: 0.9,
      api_writes: 40,
      docs_created: 5,
      approvals: 2,
      exports: 1,
      http_422_per_100_writes: 3,
      labels: [{ code: 5, score: 0.8 }],
      last_active_day: '2026-10-16',
    },
  ],
  total: 1,
  page: 1,
  page_size: 20,
  label_week: '2026-10-12',
  period: { date_from: '2026-09-17', date_to: '2026-10-16' },
  data_since: '2026-09-01',
}

function Where() {
  return <span data-testid="where">{useLocation().pathname}</span>
}

function renderPage(url = '/report/usage-profiles') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[url]}>
        <Routes>
          <Route path="/report/usage-profiles" element={<UsageProfileListPage />} />
          <Route path="/report/usage-profiles/:userId" element={<Where />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.mocked(apiGet).mockReset()
  vi.mocked(apiGet).mockResolvedValue(response)
})

describe('UsageProfileListPage', () => {
  it('shows the reference-only notice and the data-since note', async () => {
    renderPage()
    expect(await screen.findByText(/chỉ dùng tham khảo, đối chiếu với thực tế trước khi kết luận/)).toBeInTheDocument()
    expect(await screen.findByText(/Số liệu có từ ngày/)).toBeInTheDocument()
  })

  it('sends the default period and the label filter as repeated values', async () => {
    renderPage('/report/usage-profiles?department_id=3&role_id=9&label=2,5&q=tran')
    await screen.findByText('Trần Thị B')
    const [url, config] = vi.mocked(apiGet).mock.calls[0]
    expect(url).toBe('/api/usage-profiles/summary')
    expect(config?.params).toMatchObject({
      preset: 'last_30_days',
      department_id: '3',
      role_id: '9',
      label: ['2', '5'],
      q: 'tran',
      page: 1,
    })
    expect(config?.params).not.toHaveProperty('from')
  })

  it('opens the profile of the clicked row', async () => {
    renderPage()
    await userEvent.click(await screen.findByText('Trần Thị B'))
    await waitFor(() => expect(screen.getByTestId('where')).toHaveTextContent('/report/usage-profiles/7'))
  })

  it('renders the style chip with the generated label', async () => {
    renderPage()
    expect(await screen.findByText('Người thạo')).toBeInTheDocument()
    expect(screen.getByText('Thu mua (6)')).toBeInTheDocument()
  })

  it('with ?metric sends metric+sort, shows the notice, the value column and "Chưa đo được" for null (duoc-CR-650)', async () => {
    vi.mocked(apiGet).mockResolvedValue({
      ...response,
      items: [
        { ...response.items[0], metric_value: 0.9 },
        { ...response.items[0], user_id: 8, full_name: 'Lê Văn C', metric_value: null },
      ],
    })
    renderPage('/report/usage-profiles?metric=active_ratio&sort=-metric')
    await screen.findByText('Trần Thị B')
    expect(vi.mocked(apiGet).mock.calls[0][1]?.params).toMatchObject({ metric: 'active_ratio', sort: '-metric' })
    expect(screen.getByText(/Đang sắp theo:/)).toBeInTheDocument()
    expect(screen.getAllByText('90%').length).toBeGreaterThan(0)
    expect(screen.getByText('Chưa đo được')).toBeInTheDocument()
  })

  it('clearing the notice drops metric and sort from the request', async () => {
    renderPage('/report/usage-profiles?metric=logins&sort=metric')
    await screen.findByText('Trần Thị B')
    await userEvent.click(screen.getByRole('button', { name: 'Bỏ sắp theo chỉ số' }))
    await waitFor(() => expect(screen.queryByText(/Đang sắp theo:/)).not.toBeInTheDocument())
    const last = vi.mocked(apiGet).mock.calls.at(-1)?.[1]?.params
    expect(last).not.toHaveProperty('metric')
    expect(last).not.toHaveProperty('sort')
  })

  it('without ?metric never sends sort', async () => {
    renderPage()
    await screen.findByText('Trần Thị B')
    expect(vi.mocked(apiGet).mock.calls[0][1]?.params).not.toHaveProperty('sort')
  })
})
