import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { HrSettingField } from '../types/hr-setting'
import { HrSettingsForm } from './hr-settings-form'

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => false, canAny: () => false, canAccess: () => true }),
}))

/** duoc-CR-713: tab Nghỉ phép của Cài đặt nhân sự — công tắc, quyền sửa, thân lưu, chặn bấm đúp. */

const apiGet = vi.fn()
const apiPut = vi.fn()
vi.mock('@/core/api', () => ({
  apiGet: (...a: unknown[]) => apiGet(...a),
  apiPut: (...a: unknown[]) => apiPut(...a),
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
  extractErrorMessage: () => 'lỗi',
  httpClient: {},
}))
vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

const FIELDS: HrSettingField[] = [
  { key: 'employee_code_prefix', group: 'hr', tab: 'employee', type: 'code_prefix', label: 'Tiền tố mã nhân sự', value: 'NSU' },
  { key: 'leave_restrict_backdated', group: 'hr', tab: 'leave', type: 'bool', label: 'Chặn đơn nghỉ lùi ngày', value: false, hint: 'h1' },
  { key: 'leave_backdated_roles', group: 'hr', tab: 'leave', type: 'roles', label: 'Vai trò được lập đơn nghỉ lùi ngày', value: '' },
  { key: 'leave_prevent_self_approval', group: 'hr', tab: 'leave', type: 'bool', label: 'Chặn tự duyệt đơn nghỉ', value: false },
]

function renderForm(props: Partial<{ canWrite: boolean; canReadRoles: boolean; fields: HrSettingField[] }> = {}) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <HrSettingsForm fields={props.fields ?? FIELDS} canWrite={props.canWrite ?? true} canReadRoles={props.canReadRoles ?? false} />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  apiGet.mockReset().mockResolvedValue([])
  apiPut.mockReset().mockResolvedValue({ fields: FIELDS })
})

async function openLeaveTab(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole('tab', { name: 'Nghỉ phép' }))
}

describe('HrSettingsForm', () => {
  it('builds one tab per backend tab, in ERPNext order, and skips tabs without fields', () => {
    renderForm()
    expect(screen.getAllByRole('tab').map((t) => t.textContent)).toEqual(['Nhân viên', 'Nghỉ phép'])
  })

  it('keeps Save disabled until something changes, then sends only the three hr keys', async () => {
    const user = userEvent.setup()
    renderForm()
    const save = screen.getByRole('button', { name: 'Lưu' })
    expect(save).toBeDisabled()
    await openLeaveTab(user)
    await user.click(screen.getByRole('switch', { name: 'Chặn tự duyệt đơn nghỉ' }))
    expect(save).toBeEnabled()
    await user.click(save)
    await waitFor(() => expect(apiPut).toHaveBeenCalledTimes(1))
    expect(apiPut).toHaveBeenCalledWith('/api/settings', {
      values: {
        employee_code_prefix: 'NSU',
        leave_restrict_backdated: false,
        leave_backdated_roles: '',
        leave_prevent_self_approval: true,
      },
    })
  })

  it('text fields are sent trimmed with the rest of the form', async () => {
    const user = userEvent.setup()
    renderForm()
    const input = screen.getByLabelText('Tiền tố mã nhân sự')
    await user.clear(input)
    await user.type(input, ' dg ')
    await user.click(screen.getByRole('button', { name: 'Lưu' }))
    await waitFor(() => expect(apiPut).toHaveBeenCalledTimes(1))
    expect(apiPut.mock.calls[0][1].values.employee_code_prefix).toBe('dg')
  })

  it('a rapid double click saves once (ref guard, not just disabled)', async () => {
    let resolve: (v: unknown) => void = () => {}
    apiPut.mockImplementation(() => new Promise((r) => (resolve = r)))
    const user = userEvent.setup()
    renderForm()
    await openLeaveTab(user)
    await user.click(screen.getByRole('switch', { name: 'Chặn đơn nghỉ lùi ngày' }))
    const save = screen.getByRole('button', { name: 'Lưu' })
    save.click()
    save.click()
    //  `mutate` gọi hàm lưu ở nhịp sau — chờ lời gọi đầu xuất hiện rồi mới khẳng định chỉ có MỘT.
    await waitFor(() => expect(apiPut).toHaveBeenCalled())
    await new Promise((r) => setTimeout(r, 20))
    expect(apiPut).toHaveBeenCalledTimes(1)
    resolve({ fields: FIELDS })
  })

  it('without setting.write every switch is read-only and there is no Save button', async () => {
    const user = userEvent.setup()
    renderForm({ canWrite: false })
    await openLeaveTab(user)
    expect(screen.queryByRole('button', { name: 'Lưu' })).toBeNull()
    for (const s of screen.getAllByRole('switch')) expect(s).toBeDisabled()
    expect(screen.getByText(/chỉ xem được/)).toBeInTheDocument()
  })

  it('without role.read shows saved role codes as text and never calls /api/roles', async () => {
    const user = userEvent.setup()
    renderForm({
      canReadRoles: false,
      fields: FIELDS.map((f) => (f.key === 'leave_backdated_roles' ? { ...f, value: 'hr_profile,admin' } : f)),
    })
    await openLeaveTab(user)
    expect(screen.getByText('hr_profile, admin')).toBeInTheDocument()
    expect(apiGet).not.toHaveBeenCalled()
  })

  it('the role picker is disabled while the backdated switch is off', async () => {
    const user = userEvent.setup()
    renderForm({ canReadRoles: true })
    await openLeaveTab(user)
    expect(screen.getByRole('button', { name: /Chọn vai trò được miễn/ })).toBeDisabled()
  })
})
