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

//  Ai đang đăng nhập — trang khóa lại khi đó là tài khoản của chính họ.
let currentUserId = 99
vi.mock('@/core/auth/use-auth', () => ({
  useAuth: () => ({ user: { id: currentUserId } }),
}))

//  Trang chỉ cần biết «được ghi» — chốt quyền thật nằm ở backend.
vi.mock('@/core/authorization/permission-gate', () => ({
  PermissionGate: ({ children }: { children: ReactNode }) => children,
}))

vi.mock('../components/user-scope-dialog', () => ({
  UserScopeDialog: () => null,
}))

const ROLES = [
  { id: 1, code: 'admin', name: 'Quản trị hệ thống' },
  { id: 2, code: 'employee', name: 'Nhân sự' },
  { id: 3, code: 'dept_head', name: 'Trưởng phòng (duyệt PYC)' },
]

function account(roleIds: number[]) {
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

function build() {
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
  currentUserId = 99
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
        ? Promise.resolve({ ...account([2]), is_active: !khoa })
        : Promise.resolve(ROLES),
    )

    const queryClient = build()
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
        ? Promise.resolve(account(roleIds))
        : Promise.resolve(ROLES),
    )

    const queryClient = build()
    const oAdmin = await screen.findByRole('checkbox', { name: /Quản trị hệ thống/ })
    expect(oAdmin).not.toBeChecked()

    roleIds = [1, 2]
    await queryClient.refetchQueries({ queryKey: ['hr', 'users', 31] })

    expect(await screen.findByRole('checkbox', { name: /Quản trị hệ thống/ })).toBeChecked()
  })

  it('trang của CHÍNH MÌNH thì khóa lại — không tự nâng quyền được', async () => {
    //  Backend đã chặn (`core/privilege_escalation.py`), nhưng để người dùng tick
    //  thoải mái rồi mới ăn 403 lúc bấm Lưu thì họ tưởng hệ hỏng chứ không tưởng
    //  là có luật. Trước 25/08/2026 bất kỳ ai có `user.write` đều tự phong quản
    //  trị hệ thống bằng đúng một lần bấm trên trang này.
    currentUserId = 31
    apiGet.mockImplementation((url: string) =>
      url === '/api/users/31'
        ? Promise.resolve(account([2]))
        : Promise.resolve(ROLES),
    )

    build()

    expect(await screen.findByRole('checkbox', { name: /Quản trị hệ thống/ })).toBeDisabled()
    expect(screen.getByRole('button', { name: /Lưu vai trò/ })).toBeDisabled()
    expect(screen.getByText(/chốt hai người/)).toBeInTheDocument()
  })
})
