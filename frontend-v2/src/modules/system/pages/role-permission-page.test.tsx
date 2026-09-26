import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ReactNode } from 'react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { RolePermissionPage } from './role-permission-page'

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

vi.mock('@/core/auth/use-auth', () => ({
  //  Vai trò đang mở KHÔNG phải vai trò của người đang đăng nhập, nếu không
  //  trang tự khóa nút Lưu (chốt hai người của CR-158).
  useAuth: () => ({ user: { id: 99, role_ids: [] } }),
}))

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => true }),
}))

vi.mock('@/core/authorization/permission-gate', () => ({
  PermissionGate: ({ children }: { children: ReactNode }) => children,
}))

//  Ba khối con không tham gia vào chốt đang kiểm; dựng thật chỉ làm bài kiểm
//  đỏ theo những thay đổi chẳng liên quan.
vi.mock('../components/role-side-panel', () => ({ RoleSidePanel: () => null }))
vi.mock('../components/role-permission-matrix', () => ({ RolePermissionMatrix: () => null }))
vi.mock('../components/role-name-inline-edit', () => ({ RoleNameInlineEdit: () => null }))
vi.mock('../components/user-account-table', () => ({ UserAccountTable: () => null }))

const ROLES = [
  { id: 7, code: 'pur_staff', name: 'Nhân viên thu mua', description: '', sort_order: 10 },
]

const META = {
  entities: [{ key: 'purchase_request', label: 'YCMH' }, { key: 'supplier', label: 'NCC' }],
  actions: [{ key: 'read', label: 'Xem' }, { key: 'write', label: 'Sửa' }],
  scopes: [{ key: 'own', label: 'Của tôi' }, { key: 'dept', label: 'Phòng ban' }],
}

//  Vai trò 7 đang có quyền thật: đọc+ghi YCMH, chỉ đọc NCC.
const SAVED_ROWS = [
  { entity: 'purchase_request', scope: 'dept', can_read: true, can_write: true },
  { entity: 'supplier', scope: 'own', can_read: true, can_write: false },
]

function newQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
}

//  Truyền sẵn một `queryClient` khi cần dựng lại trang trên cùng bộ đệm — đó là
//  cảnh «mở lại link `?role=7`», khác hẳn cảnh vào trang lần đầu.
function build(queryClient = newQueryClient()) {
  const { unmount } = render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/system/permissions?role=7']}>
        <Routes>
          <Route path="/system/permissions" element={<RolePermissionPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )

  return { queryClient, unmount }
}

beforeEach(() => {
  apiGet.mockReset()
  httpPut.mockReset()
  httpPut.mockResolvedValue({ data: { success: true, message: 'Đã lưu quyền', data: null } })
  apiGet.mockImplementation((url: string) => {
    if (url === '/api/roles') return Promise.resolve(ROLES)
    if (url === '/api/roles/meta') return Promise.resolve(META)
    if (url === '/api/roles/7/permissions') return Promise.resolve(SAVED_ROWS)
    return Promise.resolve(null)
  })
})

describe('RolePermissionPage', () => {
  it('mở lại link `?role=` khi bộ đệm còn nóng thì KHÔNG lưu đè một ma trận rỗng', async () => {
    //  Cùng họ lỗi với bao-CR-491 (đại ca báo 25/09/2026), rà ra ở bao-CR-492 —
    //  và đây là chỗ nặng nhất của cả họ.
    //
    //  Vai trò đang mở nằm trên URL, nên vào lại trang bằng đúng link đó là
    //  `savedRows` có sẵn trong bộ đệm NGAY ở lượt render đầu. Ở lượt đầu
    //  `useHasChanged` luôn trả `false`, nên bản cũ — vốn khởi tạo state bằng
    //  `{}` rồi chờ dữ liệu «đổi» mới đổ vào — hiện ra một ma trận TRẮNG.
    //
    //  Bấm «Lưu quyền» lúc đó gửi danh sách RỖNG, mà `setPermissions` ghi đè
    //  toàn bộ (backend `role/service.set_permissions` xóa hết rồi ghi lại):
    //  mất sạch quyền của vai trò, kéo theo mọi tài khoản đang giữ nó.
    const nguoi = userEvent.setup()

    const lanDau = build()
    expect(await screen.findByRole('button', { name: /Lưu quyền/ })).toBeEnabled()

    lanDau.unmount()
    build(lanDau.queryClient)

    await nguoi.click(await screen.findByRole('button', { name: /Lưu quyền/ }))

    expect(httpPut).toHaveBeenCalledWith('/api/roles/7/permissions', {
      permissions: [
        { entity: 'purchase_request', scope: 'dept', can_read: true, can_write: true },
        { entity: 'supplier', scope: 'own', can_read: true, can_write: false },
      ],
    })
  })

  it('vai trò thật sự chưa có quyền nào thì vẫn lưu được danh sách rỗng', async () => {
    //  Mặt kia của chốt trên: khởi tạo đọc thẳng dữ liệu máy chủ nên phải phân
    //  biệt «máy chủ trả rỗng» với «chưa tải xong». Vai trò mới tinh là ca thật,
    //  không phải ca bịa.
    apiGet.mockImplementation((url: string) => {
      if (url === '/api/roles') return Promise.resolve(ROLES)
      if (url === '/api/roles/meta') return Promise.resolve(META)
      if (url === '/api/roles/7/permissions') return Promise.resolve([])
      return Promise.resolve(null)
    })
    const nguoi = userEvent.setup()

    const lanDau = build()
    expect(await screen.findByRole('button', { name: /Lưu quyền/ })).toBeEnabled()
    lanDau.unmount()
    build(lanDau.queryClient)

    await nguoi.click(await screen.findByRole('button', { name: /Lưu quyền/ }))
    expect(httpPut).toHaveBeenCalledWith('/api/roles/7/permissions', { permissions: [] })
  })
})
