import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ReactNode } from 'react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { UserPermissionDetailPage } from './user-permission-detail-page'

//  Chặn ở tầng `@/core/api` theo luật test của dự án, không chặn axios.
const apiGet = vi.fn()
const httpPut = vi.fn()

vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
  httpClient: { put: (...args: unknown[]) => httpPut(...args) },
}))

vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

//  Trang chỉ cần biết «được ghi» — chốt quyền thật nằm ở backend.
vi.mock('@/core/authorization/permission-gate', () => ({
  PermissionGate: ({ children }: { children: ReactNode }) => children,
}))

vi.mock('../components/user-scope-dialog', () => ({
  UserScopeDialog: () => null,
}))

const VAI_TRO = [
  { id: 1, code: 'admin', name: 'Quản trị hệ thống' },
  { id: 2, code: 'employee', name: 'Nhân sự' },
  { id: 3, code: 'dept_head', name: 'Trưởng phòng (duyệt PYC)' },
]

function taiKhoan(roleIds: number[]) {
  return {
    id: 31,
    email: 'ntktho@degoholding.vn',
    employee_id: 9,
    is_active: true,
    role_ids: roleIds,
    full_name: 'Nguyễn Kỳ Thảo Thơ',
    department_name: 'Phòng Công nghệ thông tin',
  }
}

function dung() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })

  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/hr/permissions/users/31']}>
        <Routes>
          <Route path="/hr/permissions/users/:userId" element={<UserPermissionDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )

  return queryClient
}

beforeEach(() => {
  apiGet.mockReset()
  httpPut.mockReset()
  httpPut.mockResolvedValue({ data: { success: true, message: 'Đã gán vai trò', data: null } })
})

describe('UserPermissionDetailPage', () => {
  it('giữ nguyên các ô vừa tick khi dữ liệu tài khoản được nạp lại giữa chừng', async () => {
    //  Lỗi khách báo 25/08/2026: «Chọn quyền, Lưu vai trò, out ra vào lại thì mất
    //  quyền đã chọn». React Query nạp lại `account` bất cứ lúc nào — hết hạn 30
    //  giây rồi mount lại, một thao tác khác gọi `invalidateQueries(['hr'])`,
    //  người khác vừa sửa cùng tài khoản. Bản cũ đồng bộ state theo MỌI lượt nạp
    //  lại, nên lượt nạp rơi vào giữa lúc đang tick là các ô vừa chọn lặng lẽ
    //  quay về bản đã lưu, rồi cú «Lưu vai trò» ghi xuống đúng bản cũ đó.
    const nguoi = userEvent.setup()
    //  ⚠️ Lượt nạp lại phải trả về dữ liệu KHÁC ĐI thì mới dựng lại được lỗi:
    //  React Query dùng structural sharing, nạp lại đúng y dữ liệu cũ thì object
    //  giữ nguyên danh tính và `useHasChanged` không nổ. Ngoài đời cái «khác đi»
    //  ấy tới rất dễ — quản trị thứ hai vừa khóa/mở tài khoản, hoặc chính người
    //  này vừa đổi hồ sơ nhân sự ở tab khác.
    let khoa = false
    apiGet.mockImplementation((url: string) =>
      url === '/api/users/31'
        ? Promise.resolve({ ...taiKhoan([2]), is_active: !khoa })
        : Promise.resolve(VAI_TRO),
    )

    const queryClient = dung()
    const oDeptHead = await screen.findByRole('checkbox', { name: /Trưởng phòng/ })

    await nguoi.click(oDeptHead)
    expect(oDeptHead).toBeChecked()

    //  Đúng nhịp hỏng: bản ghi đổi ở máy chủ trong lúc người dùng đang tick dở.
    khoa = true
    await queryClient.refetchQueries({ queryKey: ['hr', 'users', 31] })

    expect(oDeptHead).toBeChecked()

    await nguoi.click(screen.getByRole('button', { name: /Lưu vai trò/ }))
    expect(httpPut).toHaveBeenCalledWith('/api/users/31/roles', { role_ids: [2, 3] })
  })

  it('nạp lại khi CHƯA tick gì thì vẫn ăn theo máy chủ', async () => {
    //  Chốt chặn trên không được biến trang thành ô đọc một lần rồi thôi: chưa
    //  đụng vào thì người khác vừa sửa xong phải hiện ra.
    let roleIds = [2]
    apiGet.mockImplementation((url: string) =>
      url === '/api/users/31'
        ? Promise.resolve(taiKhoan(roleIds))
        : Promise.resolve(VAI_TRO),
    )

    const queryClient = dung()
    const oAdmin = await screen.findByRole('checkbox', { name: /Quản trị hệ thống/ })
    expect(oAdmin).not.toBeChecked()

    roleIds = [1, 2]
    await queryClient.refetchQueries({ queryKey: ['hr', 'users', 31] })

    expect(await screen.findByRole('checkbox', { name: /Quản trị hệ thống/ })).toBeChecked()
  })
})
