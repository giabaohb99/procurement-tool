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

//  Mặc định vai trò đang mở KHÔNG phải vai trò của người đang đăng nhập, nếu
//  không trang tự khóa nút Lưu (chốt hai người của CR-158). Bài nào cần thì đổi.
let currentRoleIds: number[] = []
vi.mock('@/core/auth/use-auth', () => ({
  useAuth: () => ({ user: { id: 99, role_ids: currentRoleIds } }),
}))

//  `canOverride` mặc định `null` = mọi `can(entity, action)` trả `true`, giữ
//  đúng hành vi cũ của các bài kiểm có sẵn. Bài kiểm tab «Báo cáo» cần tắt
//  riêng `role.read` nên phải có đường chỉnh được, không thể để nguyên hằng số.
let canOverride: ((entity: string, action: string) => boolean) | null = null
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: (entity: string, action: string) => canOverride?.(entity, action) ?? true }),
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
vi.mock('../components/report-access-tab', () => ({ ReportAccessTab: () => null }))

const ROLES = [
  { id: 1, code: 'admin', name: 'Quản trị hệ thống', description: '', sort_order: 1 },
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
function build(queryClient = newQueryClient(), roleId = 7) {
  const { unmount } = render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/system/permissions?role=${roleId}`]}>
        <Routes>
          <Route path="/system/permissions" element={<RolePermissionPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )

  return { queryClient, unmount }
}

beforeEach(() => {
  currentRoleIds = []
  canOverride = null
  apiGet.mockReset()
  httpPut.mockReset()
  httpPut.mockResolvedValue({ data: { success: true, message: 'Đã lưu quyền', data: null } })
  apiGet.mockImplementation((url: string) => {
    if (url === '/api/roles') return Promise.resolve(ROLES)
    if (url === '/api/roles/meta') return Promise.resolve(META)
    if (url === '/api/roles/7/permissions') return Promise.resolve(SAVED_ROWS)
    if (url === '/api/roles/1/permissions') return Promise.resolve(SAVED_ROWS)
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

  it('vai trò Quản trị hệ thống chỉ xem, không có nút Lưu quyền', async () => {
    //  bao-CR-523: vai trò `admin` luôn FULL. Backend từ chối mọi bản làm hụt, nên
    //  bày nút Lưu ra chỉ để người ta bỏ tick rồi ăn 400.
    currentRoleIds = [1]
    build(newQueryClient(), 1)

    expect(await screen.findByText(/Vai trò Quản trị hệ thống luôn đủ mọi quyền/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Lưu quyền/ })).not.toBeInTheDocument()
  })

  it('quản trị hệ thống sửa được ma trận của vai trò mình đang giữ', async () => {
    //  bao-CR-523: backend miễn L1 cho người giữ `admin`, giao diện không được
    //  khóa thừa.
    currentRoleIds = [1, 7]
    build()

    expect(await screen.findByRole('button', { name: /Lưu quyền/ })).toBeEnabled()
    expect(screen.queryByText(/Bạn đang giữ vai trò này/)).not.toBeInTheDocument()
  })

  it('người thường đang giữ vai trò thì vẫn bị khóa', async () => {
    currentRoleIds = [7]
    build()

    expect(await screen.findByRole('button', { name: /Lưu quyền/ })).toBeDisabled()
    expect(screen.getByText(/Bạn đang giữ vai trò này/)).toBeInTheDocument()
  })

  it('có quyền role.read thì hiện tab «Báo cáo»', async () => {
    build()
    expect(await screen.findByRole('tab', { name: 'Báo cáo' })).toBeInTheDocument()
  })

  it('không có quyền role.read thì KHÔNG hiện tab «Báo cáo» — ẩn hẳn, không chỉ khóa', async () => {
    canOverride = (entity, action) => !(entity === 'role' && action === 'read')
    build()

    expect(await screen.findByRole('button', { name: /Lưu quyền/ })).toBeEnabled()
    expect(screen.queryByRole('tab', { name: 'Báo cáo' })).not.toBeInTheDocument()
  })
})
