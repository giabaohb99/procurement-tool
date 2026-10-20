import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { JobPositionRolesPanel } from './job-position-roles-panel'

const apiGet = vi.fn()
const apiPost = vi.fn()
const httpPut = vi.fn()
vi.mock('@/core/api', () => ({
  apiGet: (...a: unknown[]) => apiGet(...a),
  apiPost: (...a: unknown[]) => apiPost(...a),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
  httpClient: { put: (...a: unknown[]) => httpPut(...a) },
}))
vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

const confirmMock = vi.fn()
vi.mock('@/shared/ui/confirm-dialog', () => ({ confirm: (...a: unknown[]) => confirmMock(...a) }))

let perms = { read: true, write: true }
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (_entity: string, action: string) => perms[action as 'read' | 'write'] ?? false,
  }),
}))

const ROLES = [
  { id: 1, code: 'admin', name: 'Quản trị hệ thống' },
  { id: 2, code: 'employee', name: 'Nhân sự' },
  { id: 3, code: 'dept_head', name: 'Trưởng phòng (duyệt PYC)' },
]

function bundle(roleIds: number[], holders = 4) {
  return {
    roles: roleIds.map((id) => ({
      role_id: id,
      role_code: ROLES.find((r) => r.id === id)!.code,
      role_name: ROLES.find((r) => r.id === id)!.name,
    })),
    eligible_holders: holders,
  }
}

function build() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <JobPositionRolesPanel positionId={7} />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  perms = { read: true, write: true }
  apiGet.mockReset()
  apiPost.mockReset()
  httpPut.mockReset()
  confirmMock.mockReset()
  apiGet.mockImplementation((url: string) =>
    Promise.resolve(url === '/api/roles' ? ROLES : bundle([2])),
  )
})

describe('JobPositionRolesPanel', () => {
  it('liệt kê gói đã lưu và nút Áp lại hiện đúng số người', async () => {
    build()
    expect(await screen.findByText('Nhân sự')).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /Áp lại cho người đang giữ chức vụ \(4 người\)/ }),
    ).toBeEnabled()
  })

  it('thêm vai trò rồi Lưu gửi cả danh sách; nút Áp lại khóa khi chưa lưu', async () => {
    const nguoi = userEvent.setup()
    httpPut.mockResolvedValue({ data: { success: true, data: bundle([2, 3]) } })
    build()
    await screen.findByText('Nhân sự')
    await nguoi.click(screen.getByRole('combobox'))
    await nguoi.click(await screen.findByText(/Trưởng phòng \(duyệt PYC\)/))
    await nguoi.click(screen.getByRole('button', { name: /Thêm/ }))
    expect(screen.getByRole('button', { name: /Áp lại cho người đang giữ chức vụ/ })).toBeDisabled()
    await nguoi.click(screen.getByRole('button', { name: /^Lưu$/ }))
    await waitFor(() => expect(httpPut).toHaveBeenCalledWith('/api/job-positions/7/roles', { role_ids: [2, 3] }))
  })

  it('bấm Lưu hai lần sát nhau chỉ gửi MỘT PUT (review L5)', async () => {
    const nguoi = userEvent.setup()
    let release: (v: unknown) => void = () => {}
    httpPut.mockReturnValue(new Promise((r) => (release = r)))
    build()
    await screen.findByText('Nhân sự')
    await nguoi.click(screen.getByRole('combobox'))
    await nguoi.click(await screen.findByText(/Trưởng phòng \(duyệt PYC\)/))
    await nguoi.click(screen.getByRole('button', { name: /Thêm/ }))
    const save = screen.getByRole('button', { name: /^Lưu$/ })
    await nguoi.dblClick(save)
    expect(httpPut).toHaveBeenCalledTimes(1)
    release({ data: { success: true, data: bundle([2, 3]) } })
  })

  it('mọi nút trong panel là type=button (review L6)', async () => {
    build()
    await screen.findByText('Nhân sự')
    for (const b of screen.getAllByRole('button')) expect(b).toHaveAttribute('type', 'button')
  })

  it('không đưa vai trò Quản trị hệ thống vào ô chọn', async () => {
    const nguoi = userEvent.setup()
    build()
    await screen.findByText('Nhân sự')
    await nguoi.click(screen.getByRole('combobox'))
    await screen.findByText(/Trưởng phòng \(duyệt PYC\)/)
    expect(screen.queryByText(/Quản trị hệ thống \(admin\)/)).not.toBeInTheDocument()
  })

  it('Áp lại phải qua hộp xác nhận; hủy thì không gọi API', async () => {
    const nguoi = userEvent.setup()
    apiPost.mockResolvedValue({ holders: 4, changed_users: 2, granted: 2, revoked: 0, skipped_self: 0, skipped_no_permission: 0 })
    build()
    await screen.findByText('Nhân sự')
    const btn = screen.getByRole('button', { name: /Áp lại cho người đang giữ chức vụ/ })
    confirmMock.mockResolvedValueOnce(false)
    await nguoi.click(btn)
    expect(apiPost).not.toHaveBeenCalled()
    confirmMock.mockResolvedValueOnce(true)
    await nguoi.click(btn)
    await waitFor(() => expect(apiPost).toHaveBeenCalledWith('/api/job-positions/7/roles/apply'))
    expect(confirmMock.mock.calls[0][0].message).toContain('4 người')
  })

  it('chỉ có quyền đọc: không có nút sửa/lưu/áp lại', async () => {
    perms = { read: true, write: false }
    build()
    await screen.findByText('Nhân sự')
    expect(screen.queryByRole('button', { name: /Lưu/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Áp lại/ })).not.toBeInTheDocument()
  })

  it('thiếu quyền đọc Vai trò: nói rõ và không gọi API', () => {
    perms = { read: false, write: false }
    build()
    expect(screen.getByText(/cần quyền xem Vai trò/)).toBeInTheDocument()
    expect(apiGet).not.toHaveBeenCalledWith('/api/job-positions/7/roles', expect.anything())
  })
})
