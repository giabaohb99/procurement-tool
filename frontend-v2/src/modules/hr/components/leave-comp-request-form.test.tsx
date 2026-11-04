import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type * as CoreApi from '@/core/api'
import { LeaveCompRequestForm } from './leave-comp-request-form'
import { LEAVE_COMP_STATUS, type LeaveCompRequest } from '../types/leave-comp'

const { apiPost, apiPatch, perm } = vi.hoisted(() => ({
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
  perm: { canReadEmployees: false },
}))

vi.mock('@/core/api', async (importOriginal) => ({
  ...(await importOriginal<typeof CoreApi>()),
  apiPost,
  apiPatch,
}))
vi.mock('@/core/auth/use-auth', () => ({ useAuth: () => ({ user: { employee_id: 5 } }) }))
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => perm.canReadEmployees }),
}))
vi.mock('../hooks/use-employees', () => ({ useEmployees: () => ({ data: undefined }) }))

const draft: LeaveCompRequest = {
  id: 9,
  code: 'NB009',
  company_id: 1,
  department_id: 1,
  department_name: 'Kho',
  employee_id: 5,
  employee_name: 'An',
  employee_code: 'NSU005',
  work_date: '2026-10-25',
  days: 1,
  reason: 'Trực kho Chủ nhật',
  status: LEAVE_COMP_STATUS.DRAFT,
  status_label: 'Nháp',
  approval_instance_id: 0,
  decided_at: null,
  decision_note: '',
  created_by: 1,
  created_at: '2026-10-25T00:00:00',
  updated_at: '2026-10-25T00:00:00',
}

function renderForm(props: Parameters<typeof LeaveCompRequestForm>[0]) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <LeaveCompRequestForm {...props} />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  perm.canReadEmployees = false
  apiPost.mockReset()
  apiPatch.mockReset()
})

describe('LeaveCompRequestForm', () => {
  it('blocks submit with inline errors and makes NO request when the date is missing', async () => {
    const user = userEvent.setup()
    renderForm({})
    await user.click(screen.getByRole('button', { name: /Gửi duyệt/ }))
    expect(await screen.findAllByRole('alert')).not.toHaveLength(0)
    expect(screen.getByText('Chọn ngày đã đi làm.')).toBeInTheDocument()
    expect(apiPost).not.toHaveBeenCalled()
    expect(apiPatch).not.toHaveBeenCalled()
  })

  it('double-clicking "Gửi duyệt" saves once and submits once (ref guard, not just isPending)', async () => {
    const user = userEvent.setup()
    const onSaved = vi.fn()
    let release: () => void = () => {}
    apiPatch.mockResolvedValue({ ...draft })
    //  Giữ lời gọi gửi duyệt lại để cú bấm thứ hai rơi vào lúc request đầu còn treo.
    apiPost.mockImplementation(
      () => new Promise((resolve) => { release = () => resolve({ ...draft, status: 2 }) }),
    )
    renderForm({ request: draft, onSaved })

    const button = screen.getByRole('button', { name: /Gửi duyệt/ })
    await user.dblClick(button)
    await user.click(button)
    await waitFor(() => expect(apiPost).toHaveBeenCalledTimes(1))
    release()

    await waitFor(() => expect(onSaved).toHaveBeenCalledWith(9))
    expect(apiPatch).toHaveBeenCalledTimes(1)
    expect(apiPost).toHaveBeenCalledTimes(1)
    expect(apiPost.mock.calls[0][0]).toBe('/api/leave-comp-requests/9/submit')
  })

  it('still reports the saved id when the submit step fails, so the page leaves the form (no duplicate create on retry)', async () => {
    const user = userEvent.setup()
    const onSaved = vi.fn()
    apiPatch.mockResolvedValue({ ...draft })
    apiPost.mockRejectedValue(new Error('422 ngày không phải ngày nghỉ'))
    renderForm({ request: draft, onSaved })

    await user.click(screen.getByRole('button', { name: /Gửi duyệt/ }))
    await waitFor(() => expect(onSaved).toHaveBeenCalledWith(9))
    //  Nút mở lại được sau lỗi.
    expect(screen.getByRole('button', { name: /Gửi duyệt/ })).toBeEnabled()
  })

  it('"Lưu nháp" only saves — it never calls submit', async () => {
    const user = userEvent.setup()
    apiPatch.mockResolvedValue({ ...draft })
    renderForm({ request: draft })
    await user.click(screen.getByRole('button', { name: /Lưu nháp/ }))
    await waitFor(() => expect(apiPatch).toHaveBeenCalledTimes(1))
    expect(apiPost).not.toHaveBeenCalled()
  })

  it('creates a new draft through POST with employee_id 0 meaning "me"', async () => {
    const user = userEvent.setup()
    //  `id: 0` = form coi như phiếu chưa lưu (cùng điều kiện `id ? update : create` của hook) nhưng đã điền sẵn ngày + lý do.
    apiPost.mockResolvedValue({ ...draft, id: 12 })
    const onSaved = vi.fn()
    renderForm({ request: { ...draft, id: 0 }, onSaved })
    await user.click(screen.getByRole('button', { name: /Lưu nháp/ }))
    await waitFor(() => expect(onSaved).toHaveBeenCalledWith(12))
    expect(apiPost).toHaveBeenCalledWith(
      '/api/leave-comp-requests',
      expect.objectContaining({ work_date: '2026-10-25', days: 1 }),
    )
  })

  it('edit mode shows the taker read-only and hides the person picker (PATCH cannot change employee)', () => {
    perm.canReadEmployees = true
    renderForm({ request: draft })
    expect(screen.getByTestId('comp-taker-readonly')).toHaveTextContent('An (NSU005)')
    expect(screen.queryByText(/Mặc định là bạn/)).not.toBeInTheDocument()
  })

  it('create mode keeps the person picker for users who may read the directory', () => {
    perm.canReadEmployees = true
    renderForm({})
    expect(screen.getByText(/Mặc định là bạn/)).toBeInTheDocument()
    expect(screen.queryByTestId('comp-taker-readonly')).not.toBeInTheDocument()
  })
})
