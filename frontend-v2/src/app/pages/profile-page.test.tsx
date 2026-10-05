import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/core/auth/auth-store'
import type { EmployeeDetail } from '@/modules/hr/types/employee'
import type { EmployeeWorkHistory, EmployeeWorkHistoryListResult } from '@/modules/hr/types/employee-work-history'
import { ProfilePage } from './profile-page'

/**
 * Hai tab chính «Quá trình công tác» / «Quyết định bổ nhiệm» (đại ca chốt
 * 03/10/2026 — tách từ tab con lồng trong thẻ cuối tab «Thông tin cá nhân»,
 * không ai thấy). Bài kiểm chỉ nhắm đúng phần mới: tab xuất hiện/ẩn theo
 * `employee_id`, mỗi tab hiện đúng khu, không nút ghi.
 *
 * KHÔNG resolve `/api/auth/me` (giữ `null`, giống `user` rỗng trong store) để
 * tab «Thông tin cá nhân» chỉ dựng khung Skeleton — tránh phải dựng cả chuỗi
 * phụ thuộc của `ProfileInfoCard`/`SignatureCard`/`EmailNotificationCard` khi
 * đó không phải phần đang kiểm. `Tabs` của Radix không mount `TabsContent` ẩn,
 * nên tab «Thông tin cá nhân» không active thì các thẻ đó cũng không dựng.
 */

const state = vi.hoisted(() => ({
  myEmployee: null as EmployeeDetail | null,
  workHistory: { items: [], can_edit: false, can_open_files: true } as EmployeeWorkHistoryListResult,
}))

vi.mock('@/core/api', () => ({
  apiGet: vi.fn((url: string) => {
    if (url === '/api/auth/me') return Promise.resolve(null)
    if (url === '/api/employees/me') return Promise.resolve(state.myEmployee)
    if (url === '/api/employees/me/work-history') return Promise.resolve(state.workHistory)
    return Promise.resolve(null)
  }),
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
  apiPut: vi.fn(),
  apiDelete: vi.fn(),
  httpClient: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() },
  downloadFile: vi.fn(),
  fetchBlobUrl: vi.fn(),
}))

function row(overrides: Partial<EmployeeWorkHistory> = {}): EmployeeWorkHistory {
  return {
    id: 7,
    employee_id: 1,
    event_type: 1,
    from_date: '2020-01-01',
    to_date: null,
    company_id: 10,
    company_name: 'DEGO',
    department_id: 20,
    department_name: 'Phòng KD',
    position_id: 30,
    position_label: 'Nhân viên',
    decision_no: '',
    decision_date: null,
    note: '',
    applied_at: null,
    file_count: 0,
    is_current: true,
    can_apply: true,
    ...overrides,
  }
}

/** Đủ trường để `useMyEmployee` coi là "đã gắn hồ sơ" — các hook con của tab
 * mới không đọc gì khác từ đối tượng này. */
function employee(): EmployeeDetail {
  return { id: 1 } as EmployeeDetail
}

function renderPage(initialPath = '/me') {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialPath]}>
        <ProfilePage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  state.myEmployee = null
  state.workHistory = { items: [], can_edit: false, can_open_files: true }
  //  Không đăng nhập thật — `can()`/`usePermission` chỉ cần không throw.
  useAuthStore.setState({ user: null })
})

describe('ProfilePage — hai tab chính quá trình công tác', () => {
  it('tài khoản CÓ hồ sơ nhân sự: hai tab chính xuất hiện ngay sau «Thông tin cá nhân»', async () => {
    state.myEmployee = employee()

    renderPage()

    await screen.findByRole('tab', { name: /Quá trình công tác/ })
    const tabs = screen.getAllByRole('tab').map((t) => t.textContent)
    const infoIdx = tabs.findIndex((t) => t?.includes('Thông tin cá nhân'))
    const workIdx = tabs.findIndex((t) => t?.includes('Quá trình công tác'))
    const decisionIdx = tabs.findIndex((t) => t?.includes('Quyết định bổ nhiệm'))
    expect(infoIdx).toBe(0)
    expect(workIdx).toBe(1)
    expect(decisionIdx).toBe(2)
  })

  it('tab «Quá trình công tác» hiện đúng khu, không nút ghi', async () => {
    state.myEmployee = employee()
    state.workHistory = { items: [row({ position_label: 'Nhân viên kinh doanh' })], can_edit: false, can_open_files: true }

    renderPage('/me?tab=work-history')

    await screen.findByText('Nhân viên kinh doanh')
    expect(screen.queryByRole('button', { name: /Thêm dòng/ })).not.toBeInTheDocument()
    //  Tab «Thông tin cá nhân» không active → không mount, không có khu quá
    //  trình công tác nào lẫn trong đó (khác bản cũ trước khi tách tab).
    expect(screen.queryByRole('heading', { name: 'Quá trình công tác' })).toBeInTheDocument()
  })

  it('tab «Quyết định bổ nhiệm» CHỈ hiện dòng có decision_no, không nút ghi', async () => {
    state.myEmployee = employee()
    state.workHistory = {
      items: [
        row({ id: 1, decision_no: 'QD-20', position_label: 'Có QĐ' }),
        row({ id: 2, decision_no: '', position_label: 'Không QĐ' }),
      ],
      can_edit: false,
      can_open_files: true,
    }

    renderPage('/me?tab=decisions')

    await screen.findByText('QD-20')
    expect(screen.queryByText('Không QĐ')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Thêm dòng/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Thêm quyết định/ })).not.toBeInTheDocument()
  })

  it('tài khoản KHÔNG gắn hồ sơ nhân sự (employee_id = 0): ẨN hai tab chính', async () => {
    state.myEmployee = null

    renderPage()

    //  Chờ truy vấn `/api/employees/me` giải quyết xong rồi mới khẳng định ẨN —
    //  không thì bài kiểm có thể chạy trước khi `hasEmployeeProfile` cập nhật.
    await screen.findByRole('tab', { name: 'Thông tin cá nhân' })
    expect(screen.queryByRole('tab', { name: /Quá trình công tác/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('tab', { name: /Quyết định bổ nhiệm/ })).not.toBeInTheDocument()
  })

  it('tài khoản KHÔNG gắn hồ sơ: mở thẳng ?tab=work-history vẫn không vào được, rơi về Thông tin cá nhân', async () => {
    state.myEmployee = null

    renderPage('/me?tab=work-history')

    const infoTab = await screen.findByRole('tab', { name: 'Thông tin cá nhân' })
    expect(infoTab).toHaveAttribute('aria-selected', 'true')
    expect(screen.queryByRole('tab', { name: /Quá trình công tác/ })).not.toBeInTheDocument()
  })
})
