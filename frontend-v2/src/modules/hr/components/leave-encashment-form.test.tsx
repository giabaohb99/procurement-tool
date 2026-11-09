import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type * as CoreApi from '@/core/api'
import {
  LEAVE_ENCASHMENT_REASON,
  LEAVE_ENCASHMENT_STATUS,
  type LeaveEncashment,
  type LeaveEncashmentPreview,
} from '../types/leave-encashment'
import { LeaveEncashmentForm } from './leave-encashment-form'

const { apiGet, apiPost, apiPatch, state } = vi.hoisted(() => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
  state: { canReadEmployees: false, previewError: null as unknown },
}))

vi.mock('@/core/api', async (importOriginal) => ({
  ...(await importOriginal<typeof CoreApi>()),
  apiGet,
  apiPost,
  apiPatch,
}))
vi.mock('@/core/auth/use-auth', () => ({ useAuth: () => ({ user: { employee_id: 5, full_name: 'An' } }) }))
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (entity: string) => (entity === 'employee' ? state.canReadEmployees : true),
  }),
}))
vi.mock('../hooks/use-employees', () => ({ useEmployees: () => ({ data: undefined }) }))

const TODAY = new Date(2026, 10, 3)

const draft: LeaveEncashment = {
  id: 9,
  code: 'TTP00009',
  company_id: 1,
  department_id: 1,
  department_name: 'Kho',
  employee_id: 5,
  employee_name: 'An',
  employee_code: 'NSU005',
  leave_type_id: 1,
  leave_type_name: 'Phép năm',
  balance_year: 2026,
  reason_kind: LEAVE_ENCASHMENT_REASON.YEAR_END,
  reason_kind_label: 'Phép dư cuối năm',
  encashment_date: null,
  days: 2,
  balance_snapshot: 0,
  encashable_snapshot: 0,
  note: '',
  status: LEAVE_ENCASHMENT_STATUS.DRAFT,
  status_label: 'Nháp',
  approval_instance_id: 0,
  decided_at: null,
  decision_note: '',
  payment_request_id: 0,
  payment_status: '',
  payment_status_label: '',
  created_by: 1,
  created_at: '2026-11-03T00:00:00',
  updated_at: '2026-11-03T00:00:00',
}

function preview(overrides: Partial<LeaveEncashmentPreview> = {}): LeaveEncashmentPreview {
  return {
    has_balance: true,
    available: 10,
    unused_carried: 2,
    already_encashed: 0,
    non_encashable_days: 5,
    max_encashable_days: 0,
    cap_remaining: null,
    encashable: 3,
    employee_id: 5,
    leave_type_id: 1,
    balance_year: 2026,
    reason_kind: 1,
    reason_kind_label: 'Phép dư cuối năm',
    ...overrides,
  }
}

function mockGets(previewData: LeaveEncashmentPreview = preview()) {
  apiGet.mockImplementation((url: string, config?: { params?: { reason_kind?: number } }) => {
    if (url === '/api/leave-types') {
      return Promise.resolve({
        total: 2,
        items: [
          { id: 1, name: 'Phép năm', allow_encashment: true },
          { id: 2, name: 'Nghỉ ốm', allow_encashment: false },
        ],
      })
    }
    if (url === '/api/leave-encashments/preview') {
      if (state.previewError) return Promise.reject(state.previewError)
      const reason = config?.params?.reason_kind ?? 1
      return Promise.resolve({ ...previewData, reason_kind: reason })
    }
    return Promise.reject(new Error(`unexpected GET ${url}`))
  })
}

function renderForm(props: Partial<Parameters<typeof LeaveEncashmentForm>[0]> = {}) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <LeaveEncashmentForm today={TODAY} {...props} />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  state.canReadEmployees = false
  state.previewError = null
  apiGet.mockReset()
  apiPost.mockReset()
  apiPatch.mockReset()
  mockGets()
})

describe('LeaveEncashmentForm', () => {
  it('blocks submit with an inline error and makes NO request when no leave type is chosen', async () => {
    const user = userEvent.setup()
    renderForm()
    await user.click(screen.getByRole('button', { name: /Gửi duyệt/ }))
    expect(screen.getByText('Chọn loại nghỉ cần thanh toán.')).toBeInTheDocument()
    expect(apiPost).not.toHaveBeenCalled()
    //  Chưa chọn loại thì không xin bản xem trước.
    expect(apiGet).not.toHaveBeenCalledWith('/api/leave-encashments/preview', expect.anything())
  })

  it('editing shows person, type and year as read-only text (backend ignores changes to them)', async () => {
    renderForm({ request: draft })
    expect(screen.getByText('An (NSU005)')).toBeInTheDocument()
    expect(screen.queryByRole('combobox', { name: 'Loại nghỉ' })).not.toBeInTheDocument()
    expect(screen.queryByRole('combobox', { name: 'Năm quỹ phép' })).not.toBeInTheDocument()
    expect(await screen.findByText(/Được thanh toán tối đa/)).toBeInTheDocument()
  })

  it('explains the year-end math line by line and the user does not subtract anything', async () => {
    renderForm({ request: draft })
    expect(await screen.findByText(/Phần mang sang từ năm trước chưa dùng/)).toBeInTheDocument()
    expect(screen.getByText(/Phải giữ lại theo loại nghỉ/)).toBeInTheDocument()
    //  Không trần năm thì không bày dòng trần.
    expect(screen.queryByText(/Trần mỗi năm/)).not.toBeInTheDocument()
  })

  it('switching to resignation re-asks the backend and drops the year-end lines (D5)', async () => {
    const user = userEvent.setup()
    renderForm({ request: draft })
    await screen.findByText(/Phải giữ lại theo loại nghỉ/)
    await user.click(screen.getByLabelText('Nghỉ việc'))
    expect(await screen.findByText(/Nghỉ việc: được thanh toán hết số ngày chưa nghỉ/)).toBeInTheDocument()
    expect(screen.queryByText(/Phải giữ lại theo loại nghỉ/)).not.toBeInTheDocument()
    expect(apiGet).toHaveBeenCalledWith(
      '/api/leave-encashments/preview',
      expect.objectContaining({ params: expect.objectContaining({ reason_kind: 2, employee_id: 5 }) }),
    )
  })

  it('"Dùng hết" fills the encashable maximum into the days box', async () => {
    const user = userEvent.setup()
    renderForm({ request: draft })
    await user.click(await screen.findByRole('button', { name: /Dùng hết 3 ngày/ }))
    expect(screen.getByLabelText(/Số ngày thanh toán/)).toHaveValue('3')
  })

  it('refuses more days than encashable, and non half-day steps, without calling the API', async () => {
    const user = userEvent.setup()
    renderForm({ request: draft })
    await screen.findByText(/Được thanh toán tối đa/)
    const input = screen.getByLabelText(/Số ngày thanh toán/)

    await user.clear(input)
    await user.type(input, '5')
    await user.click(screen.getByRole('button', { name: /Lưu nháp/ }))
    expect(screen.getByText(/tối đa 3 ngày/)).toBeInTheDocument()

    await user.clear(input)
    await user.type(input, '1,25')
    await user.click(screen.getByRole('button', { name: /Lưu nháp/ }))
    expect(screen.getByText(/bước 0,5/)).toBeInTheDocument()

    //  Lúc SỬA, ô trống là mơ hồ (PATCH null = giữ số cũ) nên bắt nhập.
    await user.clear(input)
    await user.click(screen.getByRole('button', { name: /Lưu nháp/ }))
    expect(screen.getByText('Nhập số ngày thanh toán.')).toBeInTheDocument()
    expect(apiPatch).not.toHaveBeenCalled()
  })

  it('accepts a Vietnamese decimal comma, saves once and submits once on a double click', async () => {
    const user = userEvent.setup()
    const onSaved = vi.fn()
    let release: () => void = () => {}
    apiPatch.mockResolvedValue({ ...draft, days: 2.5 })
    apiPost.mockImplementation(
      () =>
        new Promise((resolve) => {
          release = () => resolve({ ...draft, status: LEAVE_ENCASHMENT_STATUS.PENDING })
        }),
    )
    renderForm({ request: draft, onSaved })
    await screen.findByText(/Được thanh toán tối đa/)
    const input = screen.getByLabelText(/Số ngày thanh toán/)
    await user.clear(input)
    await user.type(input, '2,5')

    const submit = screen.getByRole('button', { name: /Gửi duyệt/ })
    await user.dblClick(submit)
    await waitFor(() => expect(apiPost).toHaveBeenCalledTimes(1))
    release()
    await waitFor(() => expect(onSaved).toHaveBeenCalledWith(9))

    expect(apiPatch).toHaveBeenCalledTimes(1)
    expect(apiPatch).toHaveBeenCalledWith('/api/leave-encashments/9', {
      reason_kind: 1,
      days: 2.5,
      note: '',
    })
    expect(apiPost).toHaveBeenCalledWith('/api/leave-encashments/9/submit', {})
  })

  it('shows the backend 422 sentence inside the box instead of a blank box', async () => {
    state.previewError = Object.assign(new Error('Request failed with status code 422'), {
      isAxiosError: true,
      response: {
        status: 422,
        data: { success: false, error: { code: 'HTTP_422', message: 'Nhập ngày nghỉ việc trên hồ sơ nhân sự trước' } },
      },
    })
    renderForm({ request: { ...draft, reason_kind: LEAVE_ENCASHMENT_REASON.RESIGNATION } })
    expect(await screen.findByText(/Nhập ngày nghỉ việc trên hồ sơ nhân sự/)).toBeInTheDocument()
  })

  it('tells the user when no leave type allows encashment yet', async () => {
    apiGet.mockImplementation((url: string) =>
      url === '/api/leave-types'
        ? Promise.resolve({ total: 1, items: [{ id: 2, name: 'Nghỉ ốm', allow_encashment: false }] })
        : Promise.reject(new Error('unexpected')),
    )
    renderForm()
    expect(await screen.findByText(/Chưa loại nghỉ nào bật/)).toBeInTheDocument()
  })

  it('a balance that does not exist yet says so rather than showing zeros', async () => {
    mockGets(preview({ has_balance: false, encashable: 0, available: 0 }))
    renderForm({ request: draft })
    expect(await screen.findByText(/Chưa có quỹ phép năm 2026/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Dùng hết/ })).not.toBeInTheDocument()
  })
})
