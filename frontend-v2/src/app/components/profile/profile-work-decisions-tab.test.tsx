import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { EmployeeWorkHistory, EmployeeWorkHistoryListResult } from '@/modules/hr/types/employee-work-history'
import { ProfileWorkDecisionsTab } from './profile-work-decisions-tab'

const state = vi.hoisted(() => ({
  listResult: { items: [], can_edit: false, can_open_files: true } as EmployeeWorkHistoryListResult,
  calls: [] as { url: string; config?: unknown }[],
}))

//  Cùng khuôn mock với `profile-work-history-tab.test.tsx` — tab này dùng
//  CHUNG `/me/work-history`, tự lọc dòng có `decision_no`, không gọi API riêng.
vi.mock('@/core/api', () => ({
  apiGet: vi.fn((url: string, config?: unknown) => {
    state.calls.push({ url, config })
    if (url === '/api/employees/me/work-history') return Promise.resolve(state.listResult)
    if (url === '/api/attachments') return Promise.resolve([])
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
      <MemoryRouter>
        <ProfileWorkDecisionsTab />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  state.listResult = { items: [], can_edit: false, can_open_files: true }
  state.calls = []
})

describe('ProfileWorkDecisionsTab', () => {
  it('CHỈ hiện dòng có decision_no, dùng CHUNG nguồn /me/work-history', async () => {
    state.listResult = {
      items: [
        row({ id: 1, decision_no: 'QD-20', position_label: 'Có QĐ' }),
        row({ id: 2, decision_no: '', position_label: 'Không QĐ' }),
      ],
      can_edit: false,
      can_open_files: true,
    }

    renderTab()

    await screen.findByText('QD-20')
    expect(screen.queryByText('Không QĐ')).not.toBeInTheDocument()
    expect(state.calls.filter((c) => c.url === '/api/employees/me/work-history')).toHaveLength(1)
  })

  it('rỗng → câu nhắc Phòng Nhân sự, KHÔNG nút nhảy sang tab Quá trình công tác', async () => {
    renderTab()

    expect(
      await screen.findByText('Chưa có quyết định nào — ghi số QĐ khi thêm dòng quá trình công tác.'),
    ).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Thêm ở tab Quá trình công tác' })).not.toBeInTheDocument()
  })

  it('không nút Thêm/Sửa/Xóa/Áp dù người dùng có employee.write, kể cả dạng DÒNG THỜI GIAN', async () => {
    state.listResult = {
      items: [row({ id: 1, decision_no: 'QD-21', can_apply: true })],
      can_edit: false,
      can_open_files: true,
    }

    renderTab()
    await screen.findByText('QD-21')
    expect(screen.queryByRole('button', { name: /Thêm dòng/ })).not.toBeInTheDocument()

    await userEvent.click(screen.getByRole('radio', { name: 'Dòng thời gian' }))
    expect(screen.queryByRole('button', { name: 'Sửa' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Áp vào hồ sơ' })).not.toBeInTheDocument()
  })
})
