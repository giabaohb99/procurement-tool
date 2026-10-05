import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/core/auth/auth-store'
import type { AuthUser } from '@/core/auth/auth-types'
import { rosterCell, rosterItem, rosterResponse } from '../components/work-roster-fixture'

/*  Trang «Xem lịch»: chốt các cái bẫy bộ lọc (page về 1, phân biệt rỗng vì lọc / rỗng vì chưa có gì),
    và hai danh mục mượn quyền (pháp nhân, phòng ban) phải TỰ TẮT khi thiếu quyền — không 403. */

const apiGetMock = vi.fn()
vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGetMock(...args),
}))

const { WorkRosterPage } = await import('./work-roster-page')

const IT = { id: 4, name: 'IT' }

function user(permissions: AuthUser['permissions']): AuthUser {
  return { id: 1, email: 'a@b.com', full_name: 'Tester', employee_id: 1, permissions }
}

function urlsCalled(): string[] {
  return apiGetMock.mock.calls.map((c) => String(c[0]))
}

function rosterCalls(): Record<string, unknown>[] {
  return apiGetMock.mock.calls
    .filter((c) => String(c[0]).includes('/tools/roster'))
    .map((c) => (c[1] as { params: Record<string, unknown> }).params)
}

function mockApi(roster = rosterResponse([rosterItem(1, 'An', IT, [rosterCell('2026-10-05')])])) {
  apiGetMock.mockImplementation((url: string) => {
    if (url.includes('/tools/roster')) return Promise.resolve(roster)
    if (url === '/api/companies') return Promise.resolve({ total: 1, items: [{ id: 1, code: 'D', name: 'DEGO' }] })
    if (url === '/api/departments') return Promise.resolve({ total: 1, items: [{ id: 4, code: 'IT', name: 'IT', company_id: 1 }] })
    return Promise.reject(new Error(`unexpected ${url}`))
  })
}

function renderPage(search = '?date=2026-10-07') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[`/hr/work-roster${search}`]}>
        <WorkRosterPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  apiGetMock.mockReset()
  useAuthStore.setState({ user: user({ employee: { read: true } }) })
})

describe('WorkRosterPage', () => {
  it('asks the Monday-to-Sunday week of the URL date, page 1, size 50, and omits q when empty', async () => {
    mockApi()
    renderPage('?date=2026-10-07')
    await screen.findByText('An')
    expect(rosterCalls()[0]).toMatchObject({
      from_date: '2026-10-05',
      to_date: '2026-10-11',
      company_id: 0,
      department_id: 0,
      page: 1,
      page_size: 50,
    })
    expect(rosterCalls()[0].q).toBeUndefined()
  })

  it('switching to month asks from the 1st to the last day', async () => {
    mockApi()
    renderPage('?date=2026-10-07')
    await screen.findByText('An')
    fireEvent.click(screen.getByRole('button', { name: 'Tháng' }))
    await waitFor(() =>
      expect(rosterCalls().some((p) => p.from_date === '2026-10-01' && p.to_date === '2026-10-31')).toBe(true),
    )
  })

  it('survives a corrupt URL (date=abc, mode=day, company=-5) and never sends a negative id', async () => {
    mockApi()
    renderPage('?date=abc&mode=day&company=-5&department=x')
    await screen.findByText('An')
    const first = rosterCalls()[0]
    expect(first.company_id).toBe(0)
    expect(first.department_id).toBe(0)
    expect(String(first.from_date)).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  })

  it('does not call the company/department lookups and hides both filters without permission', async () => {
    mockApi()
    renderPage()
    await screen.findByText('An')
    expect(urlsCalled().filter((u) => u === '/api/companies' || u === '/api/departments')).toEqual([])
    expect(screen.queryByRole('combobox', { name: 'Lọc theo pháp nhân' })).toBeNull()
    expect(screen.queryByRole('combobox', { name: 'Lọc theo phòng ban' })).toBeNull()
  })

  it('shows the filters and calls the lookups when permitted', async () => {
    useAuthStore.setState({
      user: user({ employee: { read: true }, company: { read: true }, department: { read: true } }),
    })
    mockApi()
    renderPage()
    await screen.findByRole('combobox', { name: 'Lọc theo pháp nhân' })
    expect(screen.getByRole('combobox', { name: 'Lọc theo phòng ban' })).toBeInTheDocument()
    expect(urlsCalled()).toContain('/api/companies')
    expect(urlsCalled()).toContain('/api/departments')
  })

  it('distinguishes an empty roster from an empty filter result', async () => {
    mockApi(rosterResponse([], 0))
    renderPage('?date=2026-10-07')
    await screen.findByText('Chưa có nhân sự nào trong phạm vi bạn được xem.')
    expect(screen.queryByRole('button', { name: 'Xóa lọc' })).toBeNull()
  })

  it('reports no filter match and lets the user clear the filter', async () => {
    mockApi(rosterResponse([], 0))
    renderPage('?date=2026-10-07&company=3')
    await screen.findByText('Không có nhân sự nào khớp bộ lọc.')
    expect(screen.getByRole('button', { name: 'Xóa lọc' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Xóa lọc' }))
    await screen.findByText('Chưa có nhân sự nào trong phạm vi bạn được xem.')
  })

  it('shows an alert with a retry button on load error instead of an empty table', async () => {
    apiGetMock.mockRejectedValue(new Error('boom'))
    renderPage()
    expect(await screen.findByRole('alert')).toHaveTextContent('Không tải được lịch làm việc')
    expect(screen.getByRole('button', { name: 'Thử lại' })).toBeInTheDocument()
  })

  it('limits the search box to 100 characters to avoid a backend 422', async () => {
    mockApi()
    renderPage()
    await screen.findByText('An')
    expect(screen.getByRole('searchbox', { name: /Tìm nhân sự/ })).toHaveAttribute('maxlength', '100')
  })
})
