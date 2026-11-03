import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/core/auth/auth-store'
import { appRoutes } from '@/shared/constants/app-routes'
import type { LeavePolicyAssignment } from '../types/leave-policy'
import { LeavePolicyAssignmentListPage } from './leave-policy-assignment-list-page'

const apiGet = vi.fn()
const apiDelete = vi.fn()
vi.mock('@/core/api', () => ({
  apiGet: (...a: unknown[]) => apiGet(...a),
  apiDelete: (...a: unknown[]) => apiDelete(...a),
  apiPost: vi.fn(),
  apiPut: vi.fn(),
  apiPatch: vi.fn(),
  extractErrorMessage: () => 'lỗi',
  httpClient: {},
}))
vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

let granted = new Set<string>()
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: (entity: string, action: string) => granted.has(`${entity}.${action}`) }),
}))

//  Ngày CỐ Ý mâu thuẫn với `state`: màn hình phải đọc `state` của backend, không tự so ngày.
const ROWS: LeavePolicyAssignment[] = [
  {
    id: 7,
    employee_id: 11,
    company_id: 1,
    policy_id: 4,
    effective_from: '2020-01-01',
    effective_to: '2020-12-31',
    note: '',
    employee_name: 'Trần An',
    employee_code: 'NSU011',
    policy_name: 'Cấp quản lý',
    state: 1,
  },
  {
    id: 8,
    employee_id: 12,
    company_id: 1,
    policy_id: 4,
    effective_from: '2099-01-01',
    effective_to: null,
    note: 'ghi chú',
    employee_name: 'Lê Bình',
    employee_code: 'NSU012',
    policy_name: 'Cấp quản lý',
    state: 3,
  },
]

function renderPage(path: string = appRoutes.hr.leavePolicyAssignments) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <LeavePolicyAssignmentListPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  useAuthStore.setState({ user: null })
  granted = new Set(['leave_balance.read'])
  apiGet.mockReset().mockImplementation((url: string) =>
    Promise.resolve(
      url === '/api/leave-policy-assignments' ? { total: 2, items: ROWS } : { total: 0, items: [] },
    ),
  )
  apiDelete.mockReset().mockResolvedValue({ balances: { created: 0, recalculated: [], kept: 0, negative_after: [] } })
})

describe('LeavePolicyAssignmentListPage (duoc-CR-717)', () => {
  it('labels the state from the backend `state`, not from comparing dates on the client', async () => {
    renderPage()
    expect(await screen.findByText('Sắp tới')).toBeInTheDocument()
    expect(screen.getByText('Đã kết thúc')).toBeInTheDocument()
    expect(screen.getByText('Không thời hạn')).toBeInTheDocument()
  })

  it('hides every write action from a read-only user', async () => {
    renderPage()
    await screen.findByText('Trần An')
    for (const name of ['Phân bổ', 'Phân bổ hàng loạt', 'Kết thúc', 'Xóa']) {
      expect(screen.queryByRole('button', { name })).not.toBeInTheDocument()
    }
  })

  it('passes the policy_id / q params from a deep link to the API as policy_id / search', async () => {
    renderPage(`${appRoutes.hr.leavePolicyAssignments}?policy_id=4&q=NSU011`)
    await screen.findByText('Trần An')
    await waitFor(() =>
      expect(apiGet).toHaveBeenCalledWith(
        '/api/leave-policy-assignments',
        expect.objectContaining({ params: expect.objectContaining({ policy_id: '4', search: 'NSU011', page: 1 }) }),
      ),
    )
  })

  it('lets a writer delete with "Tính lại hạn mức năm nay" ticked by default (D3a)', async () => {
    granted = new Set(['leave_balance.read', 'leave_balance.write'])
    const user = userEvent.setup()
    renderPage()
    await screen.findByText('Trần An')
    expect(screen.getByRole('button', { name: 'Phân bổ' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Phân bổ hàng loạt' })).toBeInTheDocument()

    await user.click(screen.getAllByRole('button', { name: 'Xóa' })[0])
    const recalc = await screen.findByRole('checkbox', { name: /Tính lại hạn mức năm nay/ })
    expect(recalc).toBeChecked()
    await user.click(screen.getByRole('button', { name: 'Xóa phân bổ' }))
    await waitFor(() =>
      expect(apiDelete).toHaveBeenCalledWith('/api/leave-policy-assignments/7', {
        params: { recalc_current_year: true },
      }),
    )
  })

  it('shows no Kết thúc / Xóa on the signed-in user\'s own row — the backend 403s self-edits (D5)', async () => {
    granted = new Set(['leave_balance.read', 'leave_balance.write'])
    useAuthStore.setState({ user: { id: 1, email: '', full_name: 'Trần An', employee_id: 11, permissions: {} } })
    renderPage()
    await screen.findByText('Trần An')
    expect(screen.getByText('Của bạn — nhờ người khác sửa')).toBeInTheDocument()
    //  Chỉ còn đúng một cặp nút — của dòng Lê Bình.
    expect(screen.getAllByRole('button', { name: 'Kết thúc' })).toHaveLength(1)
    expect(screen.getAllByRole('button', { name: 'Xóa' })).toHaveLength(1)
  })
})
