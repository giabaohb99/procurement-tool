import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { EmployeeWorkHistory, EmployeeWorkHistoryListResult, WorkHistoryFile } from '@/modules/hr/types/employee-work-history'
import { ProfileWorkHistoryTab } from './profile-work-history-tab'

const state = vi.hoisted(() => ({
  listResult: { items: [], can_edit: false, can_open_files: true } as EmployeeWorkHistoryListResult,
  files: [] as WorkHistoryFile[],
  calls: [] as { url: string; config?: unknown }[],
}))

//  Mock ở tầng `@/core/api` (không mock `axios`) — đi đúng đường thật
//  `GET /api/employees/me/work-history` và `GET /api/attachments`, không mock
//  hẳn hook để bài kiểm đầu tiên xác nhận được ĐÚNG ĐƯỜNG, KHÔNG id trong URL.
vi.mock('@/core/api', () => ({
  apiGet: vi.fn((url: string, config?: unknown) => {
    state.calls.push({ url, config })
    if (url === '/api/employees/me/work-history') return Promise.resolve(state.listResult)
    if (url === '/api/attachments') return Promise.resolve(state.files)
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

//  Có `employee.write` cũng không được wired hành động nào — mock ở đây chỉ để
//  chứng minh điều đó (tab này cố ý không dùng `usePermission`).
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => true, canAny: () => true }),
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

function renderTab() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      {/*  Khu đọc/ghi lựa chọn Bảng|Dòng thời gian qua `useUrlParamState`
           (`useSearchParams`) — cần `<Router>` bọc ngoài. */}
      <MemoryRouter>
        <ProfileWorkHistoryTab />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  state.listResult = { items: [], can_edit: false, can_open_files: true }
  state.files = []
  state.calls = []
})

describe('ProfileWorkHistoryTab', () => {
  it('gọi đúng đường /me/work-history, không id nào trong URL', async () => {
    state.listResult = { items: [row()], can_edit: false, can_open_files: true }

    renderTab()

    await screen.findByText('Nhân viên')
    expect(state.calls.some((c) => c.url === '/api/employees/me/work-history')).toBe(true)
    expect(state.calls.every((c) => !c.url.includes('/employees/1/'))).toBe(true)
  })

  it('không có nút Thêm/Sửa/Xóa/Áp dù người dùng có employee.write', async () => {
    state.listResult = { items: [row()], can_edit: false, can_open_files: true }

    renderTab()

    await screen.findByText('Nhân viên')
    expect(screen.queryByRole('button', { name: /Thêm dòng/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Sửa' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Xóa' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Áp vào hồ sơ' })).not.toBeInTheDocument()
  })

  it('danh sách rỗng → câu nhắc Phòng Nhân sự cập nhật', async () => {
    renderTab()

    expect(
      await screen.findByText('Chưa có quá trình công tác nào được ghi. Phòng Nhân sự cập nhật mục này.'),
    ).toBeInTheDocument()
  })

  it('hộp tệp mở CHỈ XEM: nút xem/tải vẫn hiện, không vùng thả, không nút xóa', async () => {
    state.listResult = { items: [row({ file_count: 2 })], can_edit: false, can_open_files: true }
    state.files = [
      { id: 1, file_id: 1, filename: 'quyet-dinh.pdf', url: '', content_type: 'application/pdf', size: 1024 },
    ]

    renderTab()

    await userEvent.click(await screen.findByRole('button', { name: '2' }))

    expect(await screen.findByText('quyet-dinh.pdf')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Xem trước/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Tải về/ })).toBeInTheDocument()
    expect(screen.queryByText(/Kéo tệp vào đây/)).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Gỡ tệp' })).not.toBeInTheDocument()
  })

  it('không nút Thêm/Sửa/Xóa/Áp ở dạng DÒNG THỜI GIAN', async () => {
    state.listResult = {
      items: [row({ id: 1, decision_no: 'QD-21', can_apply: true })],
      can_edit: false,
      can_open_files: true,
    }

    renderTab()
    await screen.findByText('QD-21')

    await userEvent.click(screen.getByRole('radio', { name: 'Dòng thời gian' }))
    expect(screen.queryByRole('button', { name: 'Sửa' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Xóa' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Áp vào hồ sơ' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Thêm dòng/ })).not.toBeInTheDocument()
  })
})
