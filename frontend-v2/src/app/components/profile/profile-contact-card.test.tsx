import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { Employee } from '@/modules/hr/types/employee'
import { ProfileContactCard } from './profile-contact-card'

/**
 * Thẻ «Liên hệ» + hộp thoại tự sửa ở Trang cá nhân (bao-CR-508).
 *
 * Canh ba thứ dễ vỡ âm thầm: thân PATCH mang khóa lạ (backend `extra="forbid"`
 * → 422 cả lần lưu), bấm đúp ra hai request + hai dòng nhật ký, và chuỗi quá
 * dài đi thẳng lên server thay vì bị chặn tại ô.
 */

//  Chặn ở tầng `@/core/api` theo luật test của dự án, không chặn axios.
const apiPatch = vi.fn()

vi.mock('@/core/api', () => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  apiPut: vi.fn(),
  apiPatch: (...args: unknown[]) => apiPatch(...args),
  apiDelete: vi.fn(),
  httpClient: {},
}))

vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

function employee(overrides: Partial<Employee> = {}): Employee {
  return {
    id: 5,
    code: 'NS005',
    full_name: 'Người Thử',
    phone: '0901000111',
    permanent_address: '12 Lê Lợi, Huế',
    current_address: '',
    //  Hồ sơ đầy đủ có hơn 30 trường, thẻ này chỉ đọc ba — ép kiểu cho gọn.
    department_id: 7,
    company_id: 3,
    bank_account_no: '999888777',
    ...overrides,
  } as Employee
}

function renderCard(emp = employee()) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <ProfileContactCard employee={emp} />
    </QueryClientProvider>,
  )
}

async function openDialog() {
  await userEvent.click(screen.getByRole('button', { name: /Sửa/ }))
  return screen.getByRole('dialog')
}

describe('ProfileContactCard', () => {
  beforeEach(() => {
    apiPatch.mockReset()
    apiPatch.mockResolvedValue(employee())
  })

  it('shows the three contact fields and marks the empty one as not yet filled', () => {
    renderCard()
    expect(screen.getByText('0901000111')).toBeInTheDocument()
    expect(screen.getByText('12 Lê Lợi, Huế')).toBeInTheDocument()
    expect(screen.getByText('Chưa cập nhật')).toBeInTheDocument()
  })

  it('opens the edit dialog prefilled with the current values', async () => {
    renderCard()
    const dialog = await openDialog()

    expect(within(dialog).getByLabelText('Số điện thoại')).toHaveValue('0901000111')
    expect(within(dialog).getByLabelText('Địa chỉ thường trú')).toHaveValue('12 Lê Lợi, Huế')
    expect(within(dialog).getByLabelText('Địa chỉ hiện nay (tạm trú)')).toHaveValue('')
  })

  it('sends only the three contact keys, trimmed, to the self-service endpoint', async () => {
    renderCard()
    const dialog = await openDialog()
    const phone = within(dialog).getByLabelText('Số điện thoại')
    await userEvent.clear(phone)
    await userEvent.type(phone, '  0987654321 ')

    await userEvent.click(within(dialog).getByRole('button', { name: /Lưu/ }))

    await waitFor(() => expect(apiPatch).toHaveBeenCalledTimes(1))
    const [url, body] = apiPatch.mock.calls[0]
    expect(url).toBe('/api/employees/me/contact')
    //  Hồ sơ đang cầm department_id / bank_account_no — không khóa nào lọt theo.
    expect(body).toEqual({
      phone: '0987654321',
      permanent_address: '12 Lê Lợi, Huế',
      current_address: '',
    })
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
  })

  it('fires a single request when the form is submitted twice in the same tick', async () => {
    //  `disabled={isPending}` chỉ đúng ở lần render sau — hai lần submit liền
    //  tay phải bị chốt `useRef` chặn, không thì ra hai dòng nhật ký.
    let release: (value: unknown) => void = () => {}
    apiPatch.mockImplementation(() => new Promise((resolve) => (release = resolve)))
    renderCard()
    const dialog = await openDialog()
    const form = dialog.querySelector('form')
    if (!form) throw new Error('Không thấy form trong hộp thoại')

    fireEvent.submit(form)
    fireEvent.submit(form)

    await waitFor(() => expect(apiPatch).toHaveBeenCalledTimes(1))
    release(employee())
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    expect(apiPatch).toHaveBeenCalledTimes(1)
  })

  it('blocks a phone number longer than the column at the field, without calling the API', async () => {
    renderCard()
    const dialog = await openDialog()
    const phone = within(dialog).getByLabelText('Số điện thoại')
    await userEvent.clear(phone)
    await userEvent.type(phone, '1'.repeat(26))

    await userEvent.click(within(dialog).getByRole('button', { name: /Lưu/ }))

    expect(await within(dialog).findByText('Số điện thoại tối đa 25 ký tự')).toBeInTheDocument()
    expect(apiPatch).not.toHaveBeenCalled()
  })

  it('keeps the dialog open when the server rejects the save', async () => {
    apiPatch.mockRejectedValue(new Error('422'))
    renderCard()
    const dialog = await openDialog()

    await userEvent.click(within(dialog).getByRole('button', { name: /Lưu/ }))

    await waitFor(() => expect(apiPatch).toHaveBeenCalledTimes(1))
    expect(screen.getByRole('dialog')).toBeInTheDocument()
  })

  it('cancel closes the dialog without saving', async () => {
    renderCard()
    const dialog = await openDialog()

    await userEvent.click(within(dialog).getByRole('button', { name: 'Hủy' }))

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(apiPatch).not.toHaveBeenCalled()
  })
})
