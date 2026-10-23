import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { Employee, EmployeeFamily } from '../types/employee'
import type { EmployeeChangeRequest } from '../types/employee-change-request'
import { SelfChangeRequestCard } from './self-change-request-card'

/**
 * Thẻ + hộp «Đề nghị sửa thông tin» ở Trang cá nhân (duoc-CR-676).
 *
 * Canh ba thứ hỏng âm thầm: gửi CẢ nhóm thay vì ô đã đổi (phòng Nhân sự đọc mười dòng «không
 * đổi»), bấm Gửi khi chưa đổi gì (backend 400 tiếng Việt nhưng tốn một lượt), và bấm đúp ra hai
 * đề nghị (lượt thứ hai ăn 409).
 */

const apiGet = vi.fn()
const apiPost = vi.fn()

vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
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

const me = {
  id: 7,
  code: 'NSU007',
  full_name: 'Người Thử',
  gender: 1,
  date_of_birth: '1990-05-01',
  marital_status: 1,
  children_count: 0,
  education_level: 4,
  bank_account_no: '0011',
  bank_name: 'VCB',
  id_number: '046090000001',
} as Employee

const families: EmployeeFamily[] = [
  {
    id: 1,
    full_name: 'Mẹ Thử',
    relation: 3,
    gender: 2,
    date_of_birth: null,
    phone: '',
    id_number: '',
    sort_order: 0,
  },
]

function pendingRequest(): EmployeeChangeRequest {
  return {
    id: 31,
    employee_id: 7,
    employee_code: 'NSU007',
    employee_name: 'Người Thử',
    status: 1,
    items: [{ group: 'bank', field: 'bank_name', before: 'VCB', after: 'ACB', current: 'VCB', masked: false }],
    families: null,
    note: '',
    reject_reason: '',
    created_at: '2026-10-20T09:30:00',
    created_by_name: 'Người Thử',
    decided_at: null,
    decided_by_name: '',
    can_decide: false,
    has_sensitive: true,
  }
}

let myRequests: EmployeeChangeRequest[] = []

function renderCard() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <SelfChangeRequestCard employee={me} />
    </QueryClientProvider>,
  )
}

async function openDialog() {
  const button = await screen.findByRole('button', { name: /Đề nghị sửa thông tin/ })
  await waitFor(() => expect(button).toBeEnabled())
  await userEvent.click(button)
  return screen.findByRole('dialog')
}

describe('SelfChangeRequestCard', () => {
  beforeEach(() => {
    myRequests = []
    apiGet.mockReset()
    apiPost.mockReset()
    confirmMock.mockReset()
    apiGet.mockImplementation((url: string) => {
      if (url.endsWith('/me/change-requests')) return Promise.resolve({ items: myRequests })
      if (url.endsWith('/me/families')) return Promise.resolve({ items: families })
      return Promise.reject(new Error(`unexpected GET ${url}`))
    })
    apiPost.mockResolvedValue(pendingRequest())
  })

  it('explains that HR approves before the profile changes', async () => {
    renderCard()
    expect(
      await screen.findByText(/phòng Nhân sự duyệt rồi mới cập nhật vào hồ sơ/),
    ).toBeInTheDocument()
    expect(await screen.findByText('Bạn chưa gửi đề nghị nào.')).toBeInTheDocument()
  })

  it('blocks submit with the backend wording when nothing was changed, and sends no request', async () => {
    renderCard()
    const dialog = await openDialog()
    await userEvent.click(within(dialog).getByRole('button', { name: /Gửi đề nghị/ }))

    expect(within(dialog).getByRole('alert')).toHaveTextContent('Không có thay đổi nào để gửi')
    expect(apiPost).not.toHaveBeenCalled()
  })

  it('sends only the edited field of the edited group', async () => {
    renderCard()
    const dialog = await openDialog()
    await userEvent.click(within(dialog).getByRole('tab', { name: 'Ngân hàng' }))
    const bankName = within(dialog).getByRole('textbox', { name: 'Ngân hàng' })
    expect(bankName).toHaveValue('VCB')
    await userEvent.clear(bankName)
    await userEvent.type(bankName, 'ACB')
    await userEvent.click(within(dialog).getByRole('button', { name: /Gửi đề nghị/ }))

    await waitFor(() => expect(apiPost).toHaveBeenCalledTimes(1))
    expect(apiPost).toHaveBeenCalledWith('/api/employees/me/change-requests', {
      bank: { bank_name: 'ACB' },
    })
  })

  it('keeps an edit made on another tab after switching tabs (Radix unmounts hidden tabs)', async () => {
    renderCard()
    const dialog = await openDialog()
    await userEvent.click(within(dialog).getByRole('tab', { name: 'Giấy tờ' }))
    const idNumber = within(dialog).getByLabelText('Số CCCD')
    await userEvent.clear(idNumber)
    await userEvent.type(idNumber, '046090000009')
    await userEvent.click(within(dialog).getByRole('tab', { name: 'Cá nhân' }))
    await userEvent.click(within(dialog).getByRole('tab', { name: 'Giấy tờ' }))
    expect(within(dialog).getByLabelText('Số CCCD')).toHaveValue('046090000009')

    await userEvent.click(within(dialog).getByRole('button', { name: /Gửi đề nghị/ }))
    await waitFor(() => expect(apiPost).toHaveBeenCalledTimes(1))
    expect(apiPost.mock.calls[0][1]).toEqual({ documents: { id_number: '046090000009' } })
  })

  it('sends one request even when Gửi is clicked twice in a row', async () => {
    //  Treo lời gọi để lượt bấm thứ hai rơi đúng lúc lượt đầu còn chạy.
    let resolvePost: (value: unknown) => void = () => undefined
    apiPost.mockImplementation(() => new Promise((resolve) => (resolvePost = resolve)))
    renderCard()
    const dialog = await openDialog()
    await userEvent.click(within(dialog).getByRole('tab', { name: 'Ngân hàng' }))
    await userEvent.type(within(dialog).getByLabelText('Chi nhánh'), 'Đà Nẵng')
    const send = within(dialog).getByRole('button', { name: /Gửi đề nghị/ })
    await userEvent.dblClick(send)

    expect(apiPost).toHaveBeenCalledTimes(1)
    resolvePost(pendingRequest())
  })

  it('locks the household tab when the current list fails to load, so a submit cannot wipe real members', async () => {
    //  Review M4: bảng rỗng vì LỖI NẠP trông y như «chưa khai ai» — thêm một người rồi gửi là
    //  duyệt xong xóa sạch thành viên thật (đề nghị thay CẢ danh sách).
    let familiesCalls = 0
    apiGet.mockImplementation((url: string) => {
      if (url.endsWith('/me/change-requests')) return Promise.resolve({ items: [] })
      if (url.endsWith('/me/families')) {
        familiesCalls += 1
        return Promise.reject(new Error('network down'))
      }
      return Promise.reject(new Error(`unexpected GET ${url}`))
    })
    renderCard()
    const dialog = await openDialog()
    await userEvent.click(within(dialog).getByRole('tab', { name: 'Hộ gia đình' }))

    const alert = await within(dialog).findByRole('alert')
    expect(alert).toHaveTextContent('Không tải được danh sách hộ gia đình')
    expect(within(dialog).queryByRole('button', { name: /Thêm dòng/ })).toBeNull()

    const callsBeforeRetry = familiesCalls
    await userEvent.click(within(dialog).getByRole('button', { name: /Thử tải lại/ }))
    await waitFor(() => expect(familiesCalls).toBeGreaterThan(callsBeforeRetry))

    //  Các tab khác vẫn gửi được, và thân gửi KHÔNG mang `families`.
    await userEvent.click(within(dialog).getByRole('tab', { name: 'Ngân hàng' }))
    await userEvent.type(within(dialog).getByLabelText('Chi nhánh'), 'Huế')
    await userEvent.click(within(dialog).getByRole('button', { name: /Gửi đề nghị/ }))
    await waitFor(() => expect(apiPost).toHaveBeenCalledTimes(1))
    expect(apiPost.mock.calls[0][1]).toEqual({ bank: { bank_branch: 'Huế' } })
  })

  it('sends the whole household list when a member is added', async () => {
    renderCard()
    const dialog = await openDialog()
    await userEvent.click(within(dialog).getByRole('tab', { name: 'Hộ gia đình' }))
    await userEvent.click(await within(dialog).findByRole('button', { name: /Thêm dòng/ }))
    const names = within(dialog).getAllByRole('textbox', { name: 'Họ tên' })
    await userEvent.type(names[1], 'Con Thử')
    await userEvent.click(within(dialog).getByRole('button', { name: /Gửi đề nghị/ }))

    await waitFor(() => expect(apiPost).toHaveBeenCalledTimes(1))
    const sent = apiPost.mock.calls[0][1] as { families: { full_name: string }[] }
    expect(sent.families.map((row) => row.full_name)).toEqual(['Mẹ Thử', 'Con Thử'])
  })

  it('disables a new request and offers withdraw while one is pending', async () => {
    myRequests = [pendingRequest()]
    confirmMock.mockResolvedValue(true)
    renderCard()

    expect(await screen.findByText('Chờ duyệt')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Đề nghị sửa thông tin/ })).toBeDisabled()
    expect(screen.getByText('ACB')).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: /Rút đề nghị/ }))
    await waitFor(() =>
      expect(apiPost).toHaveBeenCalledWith('/api/employees/me/change-requests/31/withdraw'),
    )
  })

  it('shows the reject reason of the latest request', async () => {
    myRequests = [
      { ...pendingRequest(), id: 30, status: 2 },
      { ...pendingRequest(), id: 32, status: 3, reject_reason: 'Số tài khoản không khớp tên' },
    ]
    renderCard()
    expect(await screen.findByText('Số tài khoản không khớp tên')).toBeInTheDocument()
    //  Đề nghị cuối đã xong — được gửi đề nghị mới.
    expect(screen.getByRole('button', { name: /Đề nghị sửa thông tin/ })).toBeEnabled()
  })
})
