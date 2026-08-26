import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { RoleSidePanel } from './role-side-panel'
import type { Role } from '../types/role'

const ROLES: Role[] = [
  { id: 1, code: 'admin', name: 'Quản trị hệ thống', description: '', sort_order: 1 },
  { id: 2, code: 'employee', name: 'Nhân sự', description: '', sort_order: 2 },
  { id: 3, code: 'pur_staff', name: 'Nhân viên thu mua', description: '', sort_order: 3 },
]

const saveOrder = vi.fn()
let canWrite = true

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => canWrite }),
}))

//  `PermissionGate` gọi tới auth store thật; ở đây chỉ cần nó vẽ children ra.
vi.mock('@/core/authorization/permission-gate', () => ({
  PermissionGate: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

vi.mock('../hooks/use-roles', () => ({
  useCreateRole: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useSaveRoleOrder: () => ({ mutate: saveOrder, isPending: false }),
}))

function dung() {
  render(<RoleSidePanel roles={ROLES} selectedId={null} onSelect={vi.fn()} />)
}

beforeEach(() => {
  canWrite = true
  saveOrder.mockClear()
})

describe('RoleSidePanel', () => {
  it('mỗi vai trò có tay cầm kéo; KHÔNG có nút đổi tên ở cột này', () => {
    //  Đổi tên đã dời sang tiêu đề khung bên phải (`role-name-inline-edit`):
    //  cột này rộng 260px, nhét ô nhập vào là tên dài bị cắt lúc đang gõ.
    dung()
    expect(screen.getAllByRole('button', { name: /^Kéo để đổi chỗ vai trò/ })).toHaveLength(3)
    expect(screen.queryByRole('button', { name: /^Đổi tên vai trò/ })).not.toBeInTheDocument()
  })

  it('ĐANG LỌC thì tắt kéo thả và nói rõ vì sao', async () => {
    //  Trên danh sách đã lọc, "thả A xuống dưới B" không nói được gì về những
    //  dòng đang bị ẩn nằm giữa hai dòng đó — lưu xuống là thứ tự thật khác hẳn
    //  thứ người dùng vừa nhìn thấy.
    const nguoi = userEvent.setup()
    dung()
    await nguoi.type(screen.getByPlaceholderText('Tìm vai trò…'), 'thu mua')

    expect(screen.queryByRole('button', { name: /^Kéo để đổi chỗ/ })).not.toBeInTheDocument()
    expect(screen.getByText(/Xóa từ khóa tìm để kéo/)).toBeInTheDocument()
  })

  it('thiếu quyền ghi thì không kéo được', () => {
    canWrite = false
    dung()
    expect(screen.queryByRole('button', { name: /^Kéo để đổi chỗ/ })).not.toBeInTheDocument()
  })

})
