import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { LeaveBalanceAllocateDialog } from './leave-balance-allocate-dialog'

const apiGet = vi.fn()
const apiPost = vi.fn()
vi.mock('@/core/api', () => ({
  apiGet: (...a: unknown[]) => apiGet(...a),
  apiPost: (...a: unknown[]) => apiPost(...a),
  apiPatch: vi.fn(),
  apiPut: vi.fn(),
  apiDelete: vi.fn(),
  extractErrorMessage: () => 'lỗi',
  httpClient: {},
}))
const toast = vi.hoisted(() => ({ success: vi.fn(), error: vi.fn(), warning: vi.fn() }))
vi.mock('sonner', () => ({ toast }))

let granted = new Set<string>()
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: (entity: string, action: string) => granted.has(`${entity}.${action}`) }),
}))

const LISTS: Record<string, unknown> = {
  '/api/leave-types': {
    items: [
      { id: 3, name: 'Phép năm', counts_balance: true },
      { id: 5, name: 'Không lương', counts_balance: false },
      { id: 7, name: 'Nghỉ bù', counts_balance: true },
    ],
    total: 3,
  },
  '/api/companies': { items: [{ id: 2, name: 'DEGO Holding' }], total: 1 },
  '/api/departments': { items: [{ id: 9, name: 'Kế toán' }], total: 1 },
}

const RESULT = { year: 2026, employee_count: 4, created: 4, missing_hire_date: [], missing_hire_date_count: 0 }

function renderDialog(onClose = vi.fn()) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  render(
    <QueryClientProvider client={client}>
      <LeaveBalanceAllocateDialog year={2026} onClose={onClose} />
    </QueryClientProvider>,
  )
  return onClose
}

async function pick(user: ReturnType<typeof userEvent.setup>, label: string, option: string) {
  await user.click(screen.getByRole('combobox', { name: label }))
  await user.click(await screen.findByRole('option', { name: option }))
}

beforeEach(() => {
  granted = new Set(['company.read', 'department.read'])
  apiGet.mockReset().mockImplementation((url: string, config?: { params?: Record<string, unknown> }) =>
    //  Như backend thật: phòng ban dùng chung (`company_id = 0`) nên hỏi `?company_id=` là ra RỖNG.
    Promise.resolve(
      url === '/api/departments' && config?.params?.company_id
        ? { items: [], total: 0 }
        : (LISTS[url] ?? { items: [], total: 0 }),
    ),
  )
  apiPost.mockReset().mockResolvedValue(RESULT)
  toast.success.mockReset()
})

describe('LeaveBalanceAllocateDialog (duoc-CR-717)', () => {
  it('sends only the year when every filter is left empty — same as the old one-click button', async () => {
    const user = userEvent.setup()
    const onClose = renderDialog()
    expect(screen.getByRole('heading', { name: 'Cấp quỹ phép năm 2026' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Cấp quỹ' }))
    await waitFor(() => expect(apiPost).toHaveBeenCalledTimes(1))
    //  Không gửi `0` / mảng rỗng / chuỗi "any": vắng = bỏ qua ở backend.
    expect(apiPost).toHaveBeenCalledWith('/api/leave-balances/allocate', { year: 2026 })
    await waitFor(() => expect(onClose).toHaveBeenCalled())
    expect(toast.success).toHaveBeenCalledWith('Đã cấp quỹ phép năm 2026 — thêm 4 dòng')
  })

  it('sends leave_type_ids and the four narrowing filters as numbers', async () => {
    const user = userEvent.setup()
    renderDialog()
    await user.click(screen.getByRole('button', { name: /Mọi loại nghỉ có trừ quỹ/ }))
    await user.click(await screen.findByText('Nghỉ bù'))
    await user.keyboard('{Escape}')
    await pick(user, 'Pháp nhân', 'DEGO Holding')
    await pick(user, 'Phòng ban', 'Kế toán')
    await pick(user, 'Hình thức nhân viên', 'Thử việc')
    await pick(user, 'Cấp bậc', 'Nhân viên')
    await user.click(screen.getByRole('button', { name: 'Cấp quỹ' }))
    await waitFor(() => expect(apiPost).toHaveBeenCalledTimes(1))
    expect(apiPost).toHaveBeenCalledWith('/api/leave-balances/allocate', {
      year: 2026,
      leave_type_ids: [7],
      company_id: 2,
      department_id: 9,
      employment_type: 5,
      job_level: 1,
    })
  })

  it('offers only leave types that count against a balance', async () => {
    const user = userEvent.setup()
    renderDialog()
    await user.click(screen.getByRole('button', { name: /Mọi loại nghỉ có trừ quỹ/ }))
    expect(await screen.findByText('Phép năm')).toBeInTheDocument()
    expect(screen.queryByText('Không lương')).not.toBeInTheDocument()
  })

  it('keeps the department list populated after choosing a company — departments are shared, never filtered by company (review M5)', async () => {
    //  LỖI REVIEW M5: chọn pháp nhân → `useDepartments({company_id})` → danh sách phòng ban RỖNG.
    const user = userEvent.setup()
    renderDialog()
    await pick(user, 'Pháp nhân', 'DEGO Holding')
    await pick(user, 'Phòng ban', 'Kế toán')
    expect(apiGet).not.toHaveBeenCalledWith(
      '/api/departments',
      expect.objectContaining({ params: expect.objectContaining({ company_id: expect.anything() }) }),
    )
    await user.click(screen.getByRole('button', { name: 'Cấp quỹ' }))
    await waitFor(() => expect(apiPost).toHaveBeenCalledTimes(1))
    expect(apiPost.mock.calls[0][1]).toEqual({ year: 2026, company_id: 2, department_id: 9 })
  })

  it('hides company / department pickers without the catalogue permissions', () => {
    granted = new Set()
    renderDialog()
    expect(screen.queryByRole('combobox', { name: 'Pháp nhân' })).not.toBeInTheDocument()
    expect(screen.queryByRole('combobox', { name: 'Phòng ban' })).not.toBeInTheDocument()
    expect(apiGet).not.toHaveBeenCalledWith('/api/companies', expect.anything())
  })

  it('fires a single request on a double click', async () => {
    let resolve: (v: typeof RESULT) => void = () => {}
    apiPost.mockImplementation(() => new Promise((r) => (resolve = r)))
    const user = userEvent.setup()
    renderDialog()
    const button = screen.getByRole('button', { name: 'Cấp quỹ' })
    await user.dblClick(button)
    expect(apiPost).toHaveBeenCalledTimes(1)
    resolve(RESULT)
    await waitFor(() => expect(toast.success).toHaveBeenCalled())
  })
})
