import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { PolicyPreviewItem } from '../types/leave-policy'
import { LeavePolicyBulkAssignPage } from './leave-policy-bulk-assign-page'

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
  '/api/leave-policies': { total: 1, items: [{ id: 4, code: 'CS-QL', name: 'Cấp quản lý', is_active: true }] },
  '/api/leave-types': { total: 1, items: [{ id: 1, name: 'Phép năm' }] },
}

const row = (id: number, name: string, extra: Partial<PolicyPreviewItem> = {}): PolicyPreviewItem => ({
  employee_id: id,
  code: `NSU0${id}`,
  name,
  department_name: 'Kế toán',
  hire_date: '2025-01-02',
  current: null,
  conflict: null,
  conflict_message: '',
  changes: [{ leave_type_id: 1, before: 12, after: 15 }],
  ...extra,
})

const PREVIEW = {
  total: 3,
  truncated: false,
  items: [
    row(1, 'An'),
    row(2, 'Bình', {
      conflict: 'overlap',
      conflict_message: 'Bình đang có chính sách "Cũ" (01/01/2026 → Không thời hạn)',
      current: { policy_name: 'Cũ', from: '2026-01-01', to: null },
    }),
    row(3, 'Chi'),
  ],
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <LeavePolicyBulkAssignPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

async function previewWithPolicy(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole('combobox', { name: /^Chính sách/ }))
  await user.click(await screen.findByRole('option', { name: 'Cấp quản lý (CS-QL)' }))
  await user.click(screen.getByRole('button', { name: 'Xem danh sách' }))
  await screen.findByText('Bình đang có chính sách "Cũ" (01/01/2026 → Không thời hạn)')
}

beforeEach(() => {
  granted = new Set(['leave_balance.write', 'leave_type.read'])
  apiGet.mockReset().mockImplementation((url: string) => Promise.resolve(LISTS[url] ?? { items: [], total: 0 }))
  apiPost.mockReset().mockImplementation((url: string) =>
    Promise.resolve(
      url.endsWith('/preview')
        ? PREVIEW
        : {
            created: 1,
            skipped: [{ employee_id: 3, name: 'Chi', reason: 'Chi đang có chính sách khác chồng ngày.' }],
            balances: { created: 0, recalculated: [{ leave_type_id: 1, before: 12, after: 15, employee_id: 1 }], kept: 0, negative_after: [] },
          },
    ),
  )
})

describe('LeavePolicyBulkAssignPage (duoc-CR-717)', () => {
  it('cannot preview before a policy is chosen', () => {
    renderPage()
    expect(screen.getByRole('button', { name: 'Xem danh sách' })).toBeDisabled()
    expect(screen.getByText('Chọn chính sách.')).toBeInTheDocument()
  })

  it('locks the checkbox of a conflicting row, pre-selects the others and counts them on the button', async () => {
    const user = userEvent.setup()
    renderPage()
    await previewWithPolicy(user)
    expect(apiPost).toHaveBeenCalledWith(
      '/api/leave-policy-assignments/preview',
      expect.objectContaining({ policy_id: 4, only_without_active: true }),
    )
    expect(screen.getByRole('checkbox', { name: 'Chọn Bình' })).toBeDisabled()
    expect(screen.getByRole('checkbox', { name: 'Chọn Bình' })).not.toBeChecked()
    expect(screen.getByRole('button', { name: 'Phân bổ 2 người' })).toBeEnabled()
    expect(screen.getAllByText('Phép năm 12 → 15')).toHaveLength(2)

    await user.click(screen.getByRole('checkbox', { name: 'Chọn An' }))
    expect(screen.getByRole('button', { name: 'Phân bổ 1 người' })).toBeEnabled()
    //  "Chọn tất cả" chỉ ôm người phân bổ được — không bao giờ kéo dòng vướng vào.
    await user.click(screen.getByRole('checkbox', { name: 'Chọn tất cả người phân bổ được' }))
    expect(screen.getByRole('button', { name: 'Phân bổ 2 người' })).toBeEnabled()
    await user.click(screen.getByRole('checkbox', { name: 'Bỏ chọn tất cả' }))
    expect(screen.getByRole('button', { name: 'Phân bổ 0 người' })).toBeDisabled()
  })

  it('sends only the selectable ticked ids to /bulk and lists the skipped people with reasons', async () => {
    const user = userEvent.setup()
    renderPage()
    await previewWithPolicy(user)
    await user.click(screen.getByRole('button', { name: 'Phân bổ 2 người' }))
    await waitFor(() =>
      expect(apiPost).toHaveBeenCalledWith(
        '/api/leave-policy-assignments/bulk',
        expect.objectContaining({ policy_id: 4, employee_ids: [1, 3], recalc_current_year: true }),
      ),
    )
    expect(await screen.findByText('Đã phân bổ 1 · Bỏ qua 1')).toBeInTheDocument()
    expect(screen.getByText('Chi đang có chính sách khác chồng ngày.')).toBeInTheDocument()
    expect(screen.getByText(/tính lại 1 dòng quỹ/)).toBeInTheDocument()
    //  Danh sách cũ bị dọn — phải xem lại mới phân bổ tiếp được.
    expect(screen.queryByRole('button', { name: /^Phân bổ \d+ người$/ })).not.toBeInTheDocument()
  })

  it('locks "Phân bổ" once a filter changes after previewing, until the list is reloaded', async () => {
    const user = userEvent.setup()
    renderPage()
    await previewWithPolicy(user)
    await user.click(screen.getByRole('combobox', { name: 'Cấp bậc' }))
    await user.click(await screen.findByRole('option', { name: 'Nhân viên' }))
    expect(screen.getByRole('alert')).toHaveTextContent('bấm Xem danh sách lại')
    expect(screen.getByRole('button', { name: 'Phân bổ 2 người' })).toBeDisabled()
  })

  it('warns when the preview was cut at 500 people', async () => {
    const user = userEvent.setup()
    apiPost.mockImplementation(() => Promise.resolve({ ...PREVIEW, total: 812, truncated: true }))
    renderPage()
    await previewWithPolicy(user)
    expect(screen.getByText(/Chỉ hiện 500 người đầu/)).toHaveTextContent('812')
  })
})
