import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/core/auth/auth-store'
import type { AuthUser } from '@/core/auth/auth-types'
import { rosterCell, rosterItem, rosterResponse } from '../components/work-roster-fixture'

/*  Trang "Xem lịch": chốt các cái bẫy bộ lọc (page về 1, phân biệt rỗng vì lọc / rỗng vì chưa có gì),
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

//  Mặc định: Nhân sự (`work_schedule.write`) — phạm vi xem đủ bộ lọc. Trưởng phòng / nhân viên tự đặt trong bài của mình.
const HR_KEYS = { employee: { read: true }, work_schedule: { read: true, write: true } }

beforeEach(() => {
  apiGetMock.mockReset()
  useAuthStore.setState({ user: user(HR_KEYS) })
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
      user: user({ ...HR_KEYS, company: { read: true }, department: { read: true } }),
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
  //  duoc-CR-761 — xếp ca theo ngày.
  it('a manager (personal arranging key only) opens on their own department, and department=0 on the URL means all', async () => {
    useAuthStore.setState({
      user: {
        ...user({ employee: { read: true }, company: { read: true }, department: { read: true }, work_schedule_personal: { read: true, write: true } }),
        department_id: 4,
        department_name: 'IT',
        concurrents: [
          { kind: 1, kind_label: 'Phòng ban', department_id: 7, company_id: 1, department_name: 'Kế toán', company_name: 'DEGO', position_label: '', counts_scope: true },
        ],
      },
    })
    mockApi()
    renderPage('?date=2026-10-07')
    await screen.findByText('An')
    expect(rosterCalls()[0].department_id).toBe(4)
    //  Không lọc pháp nhân, không đọc danh mục phòng ban: ô phòng ban chỉ có phòng của mình + "Các phòng của tôi".
    expect(screen.queryByRole('combobox', { name: 'Lọc theo pháp nhân' })).toBeNull()
    expect(urlsCalled().filter((u) => u === '/api/companies' || u === '/api/departments')).toEqual([])
    const actor = userEvent.setup()
    await actor.click(screen.getByRole('combobox', { name: 'Lọc theo phòng ban' }))
    expect((await screen.findAllByRole('option')).map((o) => o.textContent)).toEqual(['Các phòng của tôi', 'IT', 'Kế toán'])
    await actor.keyboard('{Escape}')
    expect(screen.getByRole('button', { name: /Chép tuần trước/ })).toBeInTheDocument()
    //  Mặc định của Trưởng phòng KHÔNG tính là "đang lọc" — không bày nút Xóa lọc vô cớ.
    expect(screen.queryByRole('button', { name: 'Xóa lọc' })).toBeNull()

    apiGetMock.mockClear()
    renderPage('?date=2026-10-07&department=0')
    await waitFor(() => expect(rosterCalls().some((p) => p.department_id === 0)).toBe(true))
  })

  it('a director (personal key read only) browses the company: department catalog of their company, no company filter, search, no shift tools', async () => {
    useAuthStore.setState({
      user: {
        ...user({ employee: { read: true }, company: { read: true }, department: { read: true }, work_schedule_personal: { read: true } }),
        company_id: 1,
        department_id: 4,
      },
    })
    mockApi()
    renderPage('?date=2026-10-07&company=3')
    await screen.findByText('An')
    expect(rosterCalls()[0]).toMatchObject({ company_id: 0, department_id: 0 })
    expect(screen.queryByRole('combobox', { name: 'Lọc theo pháp nhân' })).toBeNull()
    expect(screen.getByRole('combobox', { name: 'Lọc theo phòng ban' })).toHaveTextContent('Tất cả phòng ban')
    expect(screen.getByRole('searchbox', { name: /Tìm nhân sự/ })).toBeInTheDocument()
    const deptCall = apiGetMock.mock.calls.find((c) => c[0] === '/api/departments')
    expect((deptCall?.[1] as { params: Record<string, unknown> }).params.company_id).toBe(1)
    expect(urlsCalled()).not.toContain('/api/companies')
    expect(screen.queryByRole('button', { name: /Chép tuần trước/ })).toBeNull()
    expect(screen.queryByRole('checkbox')).toBeNull()
  })

  it('a manager pasting a link to another department is pulled back to their own', async () => {
    useAuthStore.setState({
      user: { ...user({ employee: { read: true }, work_schedule_personal: { read: true, write: true } }), department_id: 4, department_name: 'IT' },
    })
    mockApi()
    renderPage('?date=2026-10-07&department=99')
    await screen.findByText('An')
    expect(rosterCalls()[0].department_id).toBe(4)
  })

  it('staff (no schedule key) only see themselves: no filters, no search, a note, and a stale q is not sent', async () => {
    useAuthStore.setState({ user: user({ employee: { read: true }, company: { read: true }, department: { read: true } }) })
    mockApi()
    renderPage('?date=2026-10-07&q=Bình&company=3&department=4')
    await screen.findByText('An')
    expect(screen.getByText('Bạn đang xem lịch của chính mình.')).toBeInTheDocument()
    expect(screen.queryByRole('combobox')).toBeNull()
    expect(screen.queryByRole('searchbox')).toBeNull()
    expect(screen.queryByRole('checkbox')).toBeNull()
    expect(rosterCalls()[0]).toMatchObject({ company_id: 0, department_id: 0 })
    expect(rosterCalls()[0].q).toBeUndefined()
    expect(urlsCalled().filter((u) => u === '/api/companies' || u === '/api/departments')).toEqual([])
  })

  it('HR keeps "all departments" as the default', async () => {
    useAuthStore.setState({ user: { ...user({ employee: { read: true }, work_schedule: { read: true, write: true } }), department_id: 4 } })
    mockApi()
    renderPage('?date=2026-10-07')
    await screen.findByText('An')
    expect(rosterCalls()[0].department_id).toBe(0)
  })

  it('a viewer without any arranging key sees no shift tools and cells stay plain', async () => {
    useAuthStore.setState({ user: user({ employee: { read: true } }) })
    mockApi()
    renderPage('?date=2026-10-07')
    await screen.findByText('An')
    expect(screen.queryByRole('button', { name: /Chép tuần trước/ })).toBeNull()
    expect(screen.queryByRole('checkbox', { name: /Chọn An/ })).toBeNull()
  })

  it('an arranger clicks a cell to open the shift dialog', async () => {
    useAuthStore.setState({ user: user({ employee: { read: true }, work_schedule: { read: true, write: true } }) })
    mockApi()
    renderPage('?date=2026-10-07')
    await screen.findByText('An')
    fireEvent.click(screen.getByTitle(/^An · 2026-10-05/))
    expect(await screen.findByRole('dialog', { name: 'An' })).toBeInTheDocument()
  })
})
