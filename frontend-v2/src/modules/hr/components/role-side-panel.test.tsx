import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { RoleSidePanel } from './role-side-panel'
import type { Role } from '../types/role'

const VAI_TRO: Role[] = [
  { id: 1, code: 'admin', name: 'Quản trị hệ thống', description: '', sort_order: 1 },
  { id: 2, code: 'employee', name: 'Nhân sự', description: '', sort_order: 2 },
  { id: 3, code: 'pur_staff', name: 'Nhân viên thu mua', description: '', sort_order: 3 },
]

const doiTen = vi.fn()
const luuThuTu = vi.fn()
let quyenGhi = true

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => quyenGhi }),
}))

//  `PermissionGate` gọi tới auth store thật; ở đây chỉ cần nó vẽ children ra.
vi.mock('@/core/authorization/permission-gate', () => ({
  PermissionGate: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

vi.mock('../hooks/use-roles', () => ({
  useCreateRole: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useUpdateRole: () => ({ mutate: doiTen, isPending: false }),
  useSaveRoleOrder: () => ({ mutate: luuThuTu, isPending: false }),
}))

function dung() {
  render(<RoleSidePanel roles={VAI_TRO} selectedId={null} onSelect={vi.fn()} />)
}

beforeEach(() => {
  quyenGhi = true
  doiTen.mockClear()
  luuThuTu.mockClear()
})

describe('RoleSidePanel', () => {
  it('mỗi vai trò có tay cầm kéo và nút đổi tên', () => {
    dung()
    expect(screen.getAllByRole('button', { name: /^Kéo để đổi chỗ vai trò/ })).toHaveLength(3)
    expect(screen.getAllByRole('button', { name: /^Đổi tên vai trò/ })).toHaveLength(3)
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

  it('thiếu quyền ghi thì không kéo cũng không đổi tên được', () => {
    quyenGhi = false
    dung()
    expect(screen.queryByRole('button', { name: /^Kéo để đổi chỗ/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^Đổi tên vai trò/ })).not.toBeInTheDocument()
  })

  it('bấm bút chì thì đổi thành ô nhập mang sẵn tên cũ', async () => {
    const nguoi = userEvent.setup()
    dung()
    await nguoi.click(screen.getByRole('button', { name: 'Đổi tên vai trò Nhân sự' }))

    expect(screen.getByLabelText('Tên vai trò employee')).toHaveValue('Nhân sự')
  })

  it('sửa tên rồi Enter thì gọi lưu đúng một lần với tên mới', async () => {
    const nguoi = userEvent.setup()
    dung()
    await nguoi.click(screen.getByRole('button', { name: 'Đổi tên vai trò Nhân sự' }))
    const o = screen.getByLabelText('Tên vai trò employee')
    await nguoi.clear(o)
    await nguoi.type(o, 'Nhân sự & Hành chính{Enter}')

    expect(doiTen).toHaveBeenCalledTimes(1)
    expect(doiTen).toHaveBeenCalledWith({ roleId: 2, name: 'Nhân sự & Hành chính' })
  })

  it('Esc thì bỏ qua, KHÔNG lưu gì', async () => {
    const nguoi = userEvent.setup()
    dung()
    await nguoi.click(screen.getByRole('button', { name: 'Đổi tên vai trò Nhân sự' }))
    await nguoi.type(screen.getByLabelText('Tên vai trò employee'), 'xxx{Escape}')

    expect(doiTen).not.toHaveBeenCalled()
    //  Về lại dòng thường: ô nhập biến mất, tên cũ hiện nguyên.
    expect(screen.queryByLabelText('Tên vai trò employee')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Chọn vai trò Nhân sự' })).toBeInTheDocument()
  })

  it('tên để trống thì bỏ qua — vai trò không tên là một dòng trắng trong danh sách', async () => {
    const nguoi = userEvent.setup()
    dung()
    await nguoi.click(screen.getByRole('button', { name: 'Đổi tên vai trò Nhân sự' }))
    await nguoi.clear(screen.getByLabelText('Tên vai trò employee'))
    await nguoi.click(screen.getByRole('button', { name: 'Lưu tên' }))

    expect(doiTen).not.toHaveBeenCalled()
  })

  it('tên không đổi thì không gọi máy chủ', async () => {
    const nguoi = userEvent.setup()
    dung()
    await nguoi.click(screen.getByRole('button', { name: 'Đổi tên vai trò Nhân sự' }))
    await nguoi.click(screen.getByRole('button', { name: 'Lưu tên' }))

    expect(doiTen).not.toHaveBeenCalled()
  })
})
