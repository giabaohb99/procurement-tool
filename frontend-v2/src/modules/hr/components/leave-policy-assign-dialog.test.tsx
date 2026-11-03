import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { PolicyPreviewItem, PolicyPreviewPayload } from '../types/leave-policy'
import { LeavePolicyAssignDialog } from './leave-policy-assign-dialog'

const apiGet = vi.fn()
const apiPost = vi.fn()
vi.mock('@/core/api', () => ({
  apiGet: (...a: unknown[]) => apiGet(...a),
  apiPost: (...a: unknown[]) => apiPost(...a),
  apiPut: vi.fn(),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
  extractErrorMessage: () => 'lỗi',
  httpClient: {},
}))
vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

let granted = new Set<string>()
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: (entity: string, action: string) => granted.has(`${entity}.${action}`) }),
}))

const LISTS: Record<string, unknown> = {
  '/api/employees': {
    total: 2,
    items: [
      { id: 11, code: 'NSU011', full_name: 'Trần An', hire_date: '2026-03-10' },
      { id: 12, code: 'NSU012', full_name: 'Lê Bình', hire_date: null },
    ],
  },
  '/api/leave-policies': { total: 1, items: [{ id: 4, code: 'CS-QL', name: 'Cấp quản lý', is_active: true }] },
  '/api/leave-types': { total: 1, items: [{ id: 1, name: 'Phép năm' }] },
}

/** Câu trả lời `/preview` cho một người — đổi theo từng bài. */
let previewFor: (payload: PolicyPreviewPayload) => Partial<PolicyPreviewItem>

function previewItem(payload: PolicyPreviewPayload): PolicyPreviewItem {
  return {
    employee_id: payload.employee_ids?.[0] ?? 0,
    code: 'NSU011',
    name: 'Trần An',
    department_name: '',
    hire_date: '2026-03-10',
    current: null,
    conflict: null,
    conflict_message: '',
    changes: [{ leave_type_id: 1, before: 12, after: 13.5 }],
    ...previewFor(payload),
  }
}

function renderDialog() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  const onOpenChange = vi.fn()
  render(
    <QueryClientProvider client={client}>
      <LeavePolicyAssignDialog open onOpenChange={onOpenChange} />
    </QueryClientProvider>,
  )
  return onOpenChange
}

async function fillEmployeeAndPolicy(user: ReturnType<typeof userEvent.setup>, employee = 'Trần An') {
  await user.click(screen.getByRole('combobox', { name: /^Nhân sự/ }))
  await user.click(await screen.findByText(employee))
  await user.click(screen.getByRole('combobox', { name: /^Chính sách/ }))
  await user.click(await screen.findByRole('option', { name: 'Cấp quản lý (CS-QL)' }))
}

beforeEach(() => {
  granted = new Set(['employee.read', 'leave_balance.write', 'leave_type.read'])
  previewFor = () => ({})
  apiGet.mockReset().mockImplementation((url: string) => Promise.resolve(LISTS[url] ?? { items: [], total: 0 }))
  apiPost.mockReset().mockImplementation((url: string, body: PolicyPreviewPayload) =>
    Promise.resolve(
      url.endsWith('/preview')
        ? { items: [previewItem(body)], total: 1, truncated: false }
        : { assignment: { id: 1 }, balances: { created: 0, recalculated: [], kept: 0, negative_after: [] } },
    ),
  )
})

describe('LeavePolicyAssignDialog (duoc-CR-717)', () => {
  it('previews current → after for the picked person and saves with recalc ON by default (D3a)', async () => {
    const user = userEvent.setup()
    const onOpenChange = renderDialog()
    const recalc = screen.getByRole('checkbox', { name: /Tính lại hạn mức năm nay/ })
    expect(recalc).toBeChecked()
    const save = screen.getByRole('button', { name: 'Phân bổ' })
    expect(save).toBeDisabled()

    await fillEmployeeAndPolicy(user)
    expect(await screen.findByText('13,5')).toBeInTheDocument()
    expect(screen.getByText('Phép năm')).toBeInTheDocument()
    expect(apiPost).toHaveBeenCalledWith(
      '/api/leave-policy-assignments/preview',
      expect.objectContaining({ policy_id: 4, employee_ids: [11], close_previous: false, effective_to: null }),
    )

    await waitFor(() => expect(save).toBeEnabled())
    await user.click(save)
    await waitFor(() =>
      expect(apiPost).toHaveBeenCalledWith(
        '/api/leave-policy-assignments',
        expect.objectContaining({ employee_id: 11, policy_id: 4, recalc_current_year: true, close_previous: false }),
      ),
    )
    await waitFor(() => expect(onOpenChange).toHaveBeenCalledWith(false))
  })

  it('shows "Kết thúc chính sách đang hiệu lực" only on overlap, keeps it visible once ticked, and re-previews with close_previous', async () => {
    const user = userEvent.setup()
    previewFor = (p) =>
      p.close_previous
        ? { current: { policy_name: 'Cũ', from: '2026-01-01', to: null } }
        : { conflict: 'overlap', conflict_message: 'Trần An đang có chính sách "Cũ" (01/01/2026 → Không thời hạn)' }
    renderDialog()
    expect(screen.queryByRole('checkbox', { name: /Kết thúc chính sách/ })).not.toBeInTheDocument()

    await fillEmployeeAndPolicy(user)
    expect(await screen.findByRole('alert')).toHaveTextContent('đang có chính sách "Cũ"')
    expect(screen.getByRole('button', { name: 'Phân bổ' })).toBeDisabled()

    await user.click(screen.getByRole('checkbox', { name: /Kết thúc chính sách/ }))
    await waitFor(() =>
      expect(apiPost).toHaveBeenLastCalledWith(
        '/api/leave-policy-assignments/preview',
        expect.objectContaining({ close_previous: true }),
      ),
    )
    await waitFor(() => expect(screen.queryByRole('alert')).not.toBeInTheDocument())
    //  Hết chồng ngày nhưng ô vẫn còn để bỏ tick lại được.
    expect(screen.getByRole('checkbox', { name: /Kết thúc chính sách/ })).toBeChecked()
    await waitFor(() => expect(screen.getByRole('button', { name: 'Phân bổ' })).toBeEnabled())
  })

  it('locks saving when the preview says self-assignment', async () => {
    const user = userEvent.setup()
    previewFor = () => ({ conflict: 'self', conflict_message: 'x' })
    renderDialog()
    await fillEmployeeAndPolicy(user)
    expect(await screen.findByRole('alert')).toHaveTextContent('Không tự phân bổ chính sách cho chính mình')
    expect(screen.getByRole('button', { name: 'Phân bổ' })).toBeDisabled()
    expect(apiPost).not.toHaveBeenCalledWith('/api/leave-policy-assignments', expect.anything())
  })

  it('fills "Từ ngày" from the hire date, and disables that shortcut when the profile has none', async () => {
    const user = userEvent.setup()
    renderDialog()
    const shortcut = screen.getByRole('button', { name: 'Từ ngày vào làm' })
    expect(shortcut).toBeDisabled()
    await fillEmployeeAndPolicy(user)
    await user.click(shortcut)
    await waitFor(() =>
      expect(apiPost).toHaveBeenLastCalledWith(
        '/api/leave-policy-assignments/preview',
        expect.objectContaining({ effective_from: '2026-03-10' }),
      ),
    )

    await user.click(screen.getByRole('combobox', { name: /^Nhân sự/ }))
    await user.click(await screen.findByText('Lê Bình'))
    expect(screen.getByRole('button', { name: 'Từ ngày vào làm' })).toBeDisabled()
  })

  it('without employee.read it does not call the employee list and explains why', () => {
    granted = new Set(['leave_balance.write'])
    renderDialog()
    expect(screen.getByText('Cần quyền xem danh sách nhân sự để chọn người.')).toBeInTheDocument()
    expect(apiGet).not.toHaveBeenCalledWith('/api/employees', expect.anything())
  })
})
