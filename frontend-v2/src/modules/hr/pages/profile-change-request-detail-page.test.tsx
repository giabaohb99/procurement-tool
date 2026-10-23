import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/core/auth/auth-store'
import type { AuthUser } from '@/core/auth/auth-types'
import type { EmployeeChangeRequest } from '../types/employee-change-request'
import { ChangeRequestDetailView } from './profile-change-request-detail-page'

/**
 * Màn duyệt MỘT đề nghị sửa hồ sơ (duoc-CR-676).
 *
 * Canh: nút Duyệt / Từ chối chỉ hiện khi backend cho (`can_decide`) và nói lý do khi không; từ
 * chối KHÔNG gửi được khi chưa có lý do; dòng hồ sơ đã đổi sau khi gửi được gắn nhãn; ô bị che
 * không lộ «null».
 */

const apiPost = vi.fn()

vi.mock('@/core/api', () => ({
  apiGet: vi.fn(),
  apiPost: (...args: unknown[]) => apiPost(...args),
  apiPut: vi.fn(),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
  httpClient: {},
}))

vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

const confirmMock = vi.fn<(options: unknown) => Promise<boolean>>()
vi.mock('@/shared/ui/confirm-dialog', () => ({
  confirm: (options: unknown) => confirmMock(options),
}))

function request(overrides: Partial<EmployeeChangeRequest> = {}): EmployeeChangeRequest {
  return {
    id: 41,
    employee_id: 7,
    employee_code: 'NSU007',
    employee_name: 'Người Thử',
    status: 1,
    items: [
      { group: 'bank', field: 'bank_name', before: 'VCB', after: 'ACB', current: 'VCB', masked: false },
      //  Phòng Nhân sự đã sửa ô này SAU lúc nhân viên gửi.
      { group: 'personal', field: 'major', before: 'Kế toán', after: 'Tài chính', current: 'Kiểm toán', masked: false },
      { group: 'documents', field: 'id_number', before: null, after: null, current: null, masked: true },
    ],
    families: null,
    note: 'Đổi ngân hàng nhận lương',
    reject_reason: '',
    created_at: '2026-10-20T09:30:00',
    created_by_name: 'Người Thử',
    decided_at: null,
    decided_by_name: '',
    can_decide: true,
    has_sensitive: true,
    ...overrides,
  }
}

function signIn(employeeId: number, permissions: Record<string, Record<string, boolean>>) {
  useAuthStore.setState({
    user: { id: 1, employee_id: employeeId, permissions } as unknown as AuthUser,
  })
}

function renderView(data: EmployeeChangeRequest) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <ChangeRequestDetailView request={data} />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ChangeRequestDetailView', () => {
  beforeEach(() => {
    apiPost.mockReset()
    apiPost.mockResolvedValue(request({ status: 2 }))
    confirmMock.mockReset()
    signIn(99, { employee: { read: true, write: true }, employee_sensitive: { read: true } })
  })

  it('shows Duyệt and Từ chối when the backend allows a decision', () => {
    renderView(request())
    expect(screen.getByRole('button', { name: /Duyệt/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Từ chối/ })).toBeInTheDocument()
  })

  it('hides both buttons and explains self-approval when the request is the viewer’s own', () => {
    signIn(7, { employee: { read: true, write: true }, employee_sensitive: { read: true } })
    renderView(request({ can_decide: false }))
    expect(screen.queryByRole('button', { name: /^Duyệt$/ })).toBeNull()
    expect(screen.queryByRole('button', { name: /Từ chối/ })).toBeNull()
    expect(screen.getByRole('note')).toHaveTextContent('đề nghị sửa hồ sơ của chính bạn')
  })

  it('explains the missing sensitive permission when that is why the decision is blocked', () => {
    signIn(99, { employee: { read: true, write: true } })
    renderView(request({ can_decide: false }))
    expect(screen.queryByRole('button', { name: /Từ chối/ })).toBeNull()
    expect(screen.getByRole('note')).toHaveTextContent('cần quyền xem thông tin nhạy cảm')
  })

  it('shows no buttons and no blocked note once the request is decided', () => {
    renderView(request({ status: 2, can_decide: true, decided_at: '2026-10-21T10:00:00' }))
    expect(screen.queryByRole('button', { name: /Từ chối/ })).toBeNull()
    expect(screen.queryByRole('note')).toBeNull()
  })

  it('flags a field changed after submission and masks hidden values without printing null', () => {
    renderView(request())
    expect(screen.getByText('Đã đổi sau khi gửi')).toBeInTheDocument()
    expect(screen.getAllByText('Đã ẩn (cần quyền xem thông tin nhạy cảm)').length).toBeGreaterThan(0)
    expect(screen.queryByText('null')).toBeNull()
  })

  it('survives a masked household list, which the backend sends as null lists', () => {
    //  `change_request_view.serialize`: thiếu quyền nhạy cảm → before/after = None, không phải [].
    renderView(request({ items: [], families: { before: null, after: null, masked: true } }))
    expect(screen.getByText('Hộ gia đình')).toBeInTheDocument()
    expect(screen.getByText('Đã ẩn (cần quyền xem thông tin nhạy cảm)')).toBeInTheDocument()
  })

  it('shows household before/after tables side by side when readable', () => {
    renderView(
      request({
        items: [],
        families: {
          before: [{ full_name: 'Mẹ Thử', relation: 3, gender: 2, date_of_birth: null, phone: '', id_number: '' }],
          after: [
            { full_name: 'Mẹ Thử', relation: 3, gender: 2, date_of_birth: null, phone: '', id_number: '' },
            { full_name: 'Con Thử', relation: 6, gender: 1, date_of_birth: '2015-02-03', phone: '', id_number: '' },
          ],
          masked: false,
        },
      }),
    )
    expect(screen.getByText('Lúc gửi (1 người)')).toBeInTheDocument()
    expect(screen.getByText('Đề nghị (2 người)')).toBeInTheDocument()
    expect(screen.getByText('Con trai')).toBeInTheDocument()
  })

  it('flags a household list that HR changed after submission', () => {
    const row = { full_name: 'Mẹ Thử', relation: 3, gender: 2, date_of_birth: null, phone: '', id_number: '' }
    renderView(
      request({
        items: [],
        families: {
          before: [row],
          current: [row, { ...row, full_name: 'Cha Thử', relation: 2, gender: 1 }],
          after: [{ ...row, id_number: '0123' }],
          masked: false,
        },
      }),
    )
    expect(screen.getByText('Hiện tại (2 người)')).toBeInTheDocument()
    expect(screen.getByText('Đã đổi sau khi gửi')).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent('Hộ gia đình trên hồ sơ đã đổi sau lúc nhân viên gửi')
  })

  it('does not flag the household when the current list only differs by blank rows or spaces', () => {
    const row = { full_name: 'Mẹ Thử', relation: 3, gender: 2, date_of_birth: null, phone: '', id_number: '' }
    renderView(
      request({
        items: [],
        families: { before: [row], current: [{ ...row, full_name: ' Mẹ Thử ' }], after: [], masked: false },
      }),
    )
    expect(screen.queryByText('Đã đổi sau khi gửi')).toBeNull()
  })

  it('keeps the 409 reason on screen when approval is refused', async () => {
    confirmMock.mockResolvedValueOnce(true)
    apiPost.mockRejectedValueOnce({
      response: {
        status: 409,
        data: { success: false, error: { code: 'CONFLICT', message: 'Hộ gia đình đã đổi sau lúc gửi.' } },
      },
    })
    renderView(request())
    await userEvent.click(screen.getByRole('button', { name: /^Duyệt$/ }))

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('Hộ gia đình đã đổi sau lúc gửi')
    expect(alert).toHaveTextContent('từ chối và nhờ nhân viên gửi lại')
  })

  it('cannot reject without a reason, then sends the trimmed reason', async () => {
    renderView(request())
    await userEvent.click(screen.getByRole('button', { name: /Từ chối/ }))
    const dialog = await screen.findByRole('dialog')
    const confirmButton = within(dialog).getByRole('button', { name: 'Từ chối' })
    expect(confirmButton).toBeDisabled()

    const reason = within(dialog).getByLabelText('Lý do từ chối')
    await userEvent.type(reason, '   ')
    expect(confirmButton).toBeDisabled()
    expect(reason).toHaveAttribute('maxLength', '500')

    await userEvent.type(reason, 'Số tài khoản không khớp tên ')
    await userEvent.click(confirmButton)
    await waitFor(() =>
      expect(apiPost).toHaveBeenCalledWith('/api/employees/change-requests/41/reject', {
        reason: 'Số tài khoản không khớp tên',
      }),
    )
  })

  it('approves only after the confirmation is accepted', async () => {
    confirmMock.mockResolvedValueOnce(false)
    renderView(request())
    await userEvent.click(screen.getByRole('button', { name: /^Duyệt$/ }))
    await waitFor(() => expect(confirmMock).toHaveBeenCalledTimes(1))
    expect(apiPost).not.toHaveBeenCalled()

    confirmMock.mockResolvedValueOnce(true)
    await userEvent.click(screen.getByRole('button', { name: /^Duyệt$/ }))
    await waitFor(() =>
      expect(apiPost).toHaveBeenCalledWith('/api/employees/change-requests/41/approve'),
    )
  })
})
