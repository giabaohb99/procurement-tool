import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ProfileEmergencyContacts } from './profile-emergency-contacts'

/**
 * Người báo tin của CHÍNH MÌNH ở Trang cá nhân (bao-CR-508).
 *
 * Phải đi cửa `/api/employees/me/contacts` — không phải `/{id}/contacts` của
 * phòng Nhân sự (gác `employee.write` + `employee_sensitive.read`, người dùng
 * thường ăn 403). Và bấm «Lưu danh sách» dồn dập chỉ được ra MỘT lần đặt lại.
 */

const apiGet = vi.fn()
const apiPut = vi.fn()

vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiPost: vi.fn(),
  apiPut: (...args: unknown[]) => apiPut(...args),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
  httpClient: {},
}))

vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

const SAVED = [
  { id: 41, full_name: 'Nguyễn Văn Cha', relation: 0, phone: '0901', address: 'Huế', sort_order: 0 },
]

function renderEditor(employeeId = 5) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <ProfileEmergencyContacts employeeId={employeeId} />
    </QueryClientProvider>,
  )
}

describe('ProfileEmergencyContacts', () => {
  beforeEach(() => {
    apiGet.mockReset()
    apiPut.mockReset()
    apiGet.mockResolvedValue(SAVED)
    apiPut.mockResolvedValue(SAVED)
  })

  it('reads from the self-service endpoint, not the HR one', async () => {
    renderEditor()
    expect(await screen.findByDisplayValue('Nguyễn Văn Cha')).toBeInTheDocument()
    expect(apiGet).toHaveBeenCalledWith('/api/employees/me/contacts')
  })

  it('does not call the API at all for an account without a linked employee', () => {
    renderEditor(0)
    expect(apiGet).not.toHaveBeenCalled()
  })

  it('saves the whole list once, without row ids, even when clicked repeatedly', async () => {
    let release: (value: unknown) => void = () => {}
    apiPut.mockImplementation(() => new Promise((resolve) => (release = resolve)))
    renderEditor()
    const save = await screen.findByRole('button', { name: /Lưu danh sách/ })

    //  Ba cú bấm trong cùng một nhịp: `disabled` chưa kịp render lại.
    save.click()
    save.click()
    save.click()

    await waitFor(() => expect(apiPut).toHaveBeenCalledTimes(1))
    const [url, body] = apiPut.mock.calls[0]
    expect(url).toBe('/api/employees/me/contacts')
    expect(body).toEqual({
      items: [{ full_name: 'Nguyễn Văn Cha', relation: 0, phone: '0901', address: 'Huế' }],
    })
    release(SAVED)
  })

  it('lets the user add a row and sends it in order', async () => {
    renderEditor()
    await screen.findByDisplayValue('Nguyễn Văn Cha')

    await userEvent.click(screen.getByRole('button', { name: /Thêm dòng/ }))
    const nameInputs = screen.getAllByLabelText('Họ tên')
    await userEvent.type(nameInputs[1], 'Trần Thị Mẹ')
    await userEvent.click(screen.getByRole('button', { name: /Lưu danh sách/ }))

    await waitFor(() => expect(apiPut).toHaveBeenCalledTimes(1))
    const names = (apiPut.mock.calls[0][1] as { items: { full_name: string }[] }).items.map(
      (r) => r.full_name,
    )
    expect(names).toEqual(['Nguyễn Văn Cha', 'Trần Thị Mẹ'])
  })
})
