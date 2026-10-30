import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/core/auth/auth-store'
import type { EmployeeDetail } from '@/modules/hr/types/employee'
import type { EmployeeWorkHistory, EmployeeWorkHistoryListResult } from '@/modules/hr/types/employee-work-history'
import { ProfilePage } from './profile-page'

/**
 * Hai mục "Quá trình công tác" / "Quyết định bổ nhiệm" (đại ca chốt
 * 03/10/2026 — tách từ tab con lồng trong thẻ cuối tab "Thông tin cá nhân",
 * không ai thấy): mục xuất hiện/ẩn theo `employee_id`, mỗi mục hiện đúng khu,
 * không nút ghi. Từ P0 doc 21 (17/10/2026) các mục nằm ở thanh bên trái 4 nhóm
 * thay cho dải tab ngang — bài kiểm đọc thanh bên, không đọc `role=tab`.
 *
 * KHÔNG resolve `/api/auth/me` (giữ `null`, giống `user` rỗng trong store) để
 * mục "Thông tin cá nhân" chỉ dựng khung Skeleton — tránh phải dựng cả chuỗi
 * phụ thuộc của `ProfileInfoCard`/`SignatureCard`/`EmailNotificationCard` khi
 * đó không phải phần đang kiểm. Trang chỉ dựng mục đang mở, nên mục "Thông
 * tin cá nhân" không mở thì các thẻ đó cũng không dựng.
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

/** Nút của các mục trong thanh bên trái (khổ máy tính). */
function navButtons() {
  return within(screen.getByRole('navigation', { name: 'Các mục trang cá nhân' })).getAllByRole('button')
}

beforeEach(() => {
  state.myEmployee = null
  state.workHistory = { items: [], can_edit: false, can_open_files: true }
  //  Không đăng nhập thật — `can()`/`usePermission` chỉ cần không throw.
  useAuthStore.setState({ user: null })
})

describe('ProfilePage — hai mục quá trình công tác', () => {
  it('tài khoản CÓ hồ sơ nhân sự: hai mục xuất hiện ngay sau "Thông tin cá nhân"', async () => {
    state.myEmployee = employee()

    renderPage()

    await screen.findByRole('button', { name: /Quá trình công tác/ })
    const tabs = navButtons().map((t) => t.textContent)
    const infoIdx = tabs.findIndex((t) => t?.includes('Thông tin cá nhân'))
    const workIdx = tabs.findIndex((t) => t?.includes('Quá trình công tác'))
    const decisionIdx = tabs.findIndex((t) => t?.includes('Quyết định bổ nhiệm'))
    expect(infoIdx).toBe(0)
    expect(workIdx).toBe(1)
    expect(decisionIdx).toBe(2)
  })

  it('tab "Quá trình công tác" hiện đúng khu, không nút ghi', async () => {
    state.myEmployee = employee()
    state.workHistory = { items: [row({ position_label: 'Nhân viên kinh doanh' })], can_edit: false, can_open_files: true }

    renderPage('/me?tab=work-history')

    await screen.findByText('Nhân viên kinh doanh')
    expect(screen.queryByRole('button', { name: /Thêm dòng/ })).not.toBeInTheDocument()
    //  Mục "Thông tin cá nhân" không mở → không mount, không có khu quá
    //  trình công tác nào lẫn trong đó (khác bản cũ trước khi tách tab).
    expect(screen.getAllByRole('heading', { name: 'Quá trình công tác' }).length).toBeGreaterThan(0)
  })

  it('tab "Quyết định bổ nhiệm" CHỈ hiện dòng có decision_no, không nút ghi', async () => {
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

  it('tài khoản KHÔNG gắn hồ sơ nhân sự (employee_id = 0): ẨN hai mục', async () => {
    state.myEmployee = null

    renderPage()

    //  Chờ truy vấn `/api/employees/me` giải quyết xong rồi mới khẳng định ẨN —
    //  không thì bài kiểm có thể chạy trước khi `hasEmployeeProfile` cập nhật.
    await screen.findByRole('button', { name: 'Thông tin cá nhân' })
    expect(screen.queryByRole('button', { name: /Quá trình công tác/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Quyết định bổ nhiệm/ })).not.toBeInTheDocument()
  })

  it('tài khoản KHÔNG gắn hồ sơ: mở thẳng ?tab=work-history vẫn không vào được, rơi về Thông tin cá nhân', async () => {
    state.myEmployee = null

    renderPage('/me?tab=work-history')

    const infoButton = await screen.findByRole('button', { name: 'Thông tin cá nhân' })
    expect(infoButton).toHaveAttribute('aria-current', 'page')
    expect(screen.queryByRole('button', { name: /Quá trình công tác/ })).not.toBeInTheDocument()
  })
})

describe('ProfilePage — thanh bên 4 nhóm (P0 doc 21)', () => {
  it('đặt "Kết nối AI riêng" đầu nhóm Trợ lý AI và mở được bằng ?tab=ai-connect', async () => {
    renderPage('/me?tab=ai-connect')

    const connect = await screen.findByRole('button', { name: 'Kết nối AI riêng' })
    expect(connect).toHaveAttribute('aria-current', 'page')
    const labels = navButtons().map((b) => b.textContent)
    expect(labels.indexOf('Kết nối AI riêng')).toBe(labels.indexOf('Khóa model AI') - 1)
    expect(screen.getByRole('heading', { level: 2, name: 'Kết nối AI riêng' })).toBeInTheDocument()
  })

  it('link cũ ?tab=ai-key (tab "Khóa AI") mở mục "Khóa model AI"', async () => {
    renderPage('/me?tab=ai-key')

    expect(await screen.findByRole('heading', { level: 2, name: 'Khóa model AI' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Khóa model AI' })).toHaveAttribute('aria-current', 'page')
  })

  it('bấm một mục ở thanh bên thì đổi nội dung và chỉ một mục được đánh dấu đang mở', async () => {
    renderPage()

    await userEvent.click(await screen.findByRole('button', { name: 'Giao diện' }))

    expect(screen.getByRole('heading', { level: 2, name: 'Giao diện' })).toBeInTheDocument()
    const current = navButtons().filter((b) => b.getAttribute('aria-current') === 'page')
    expect(current.map((b) => b.textContent)).toEqual(['Giao diện'])
  })

  it('có ô chọn mục cho điện thoại, ghi đúng mục đang mở', async () => {
    renderPage('/me?tab=devices')

    const select = await screen.findByRole('combobox', { name: 'Chọn mục trang cá nhân' })
    expect(select).toHaveTextContent('Thiết bị của tôi')
  })
})
