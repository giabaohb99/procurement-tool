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
  extractErrorMessage: (error: { response?: { data?: { error?: { message?: string } } } }) =>
    error?.response?.data?.error?.message ?? 'Có lỗi xảy ra',
}))

const toastError = vi.fn()
vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: (...a: unknown[]) => toastError(...a) } }))

//  Hộp xác nhận toàn cục — trả lời hộ người dùng.
const confirmMock = vi.fn()
vi.mock('@/shared/ui/confirm-dialog', () => ({
  confirm: (...args: unknown[]) => confirmMock(...args),
}))

//  Ai đang đăng nhập — trang khóa lại khi đó là tài khoản của chính họ, TRỪ
//  khi họ giữ vai trò Quản trị hệ thống (bao-CR-523).
let currentUserId = 99
let currentRoleIds: number[] = []
vi.mock('@/core/auth/use-auth', () => ({
  useAuth: () => ({ user: { id: currentUserId, role_ids: currentRoleIds } }),
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

function newQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
}

//  Truyền sẵn một `queryClient` khi cần dựng lại trang trên cùng bộ đệm — đó là
//  cảnh «back ra rồi vào lại», khác hẳn cảnh mở trang lần đầu.
function build(queryClient = newQueryClient()) {
  const { unmount } = render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/system/permissions/users/31']}>
        <Routes>
          <Route path="/system/permissions/users/:userId" element={<UserPermissionDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )

  return { queryClient, unmount }
}

const SILENT = { _silent: true }

const SELF_ADMIN_QUESTION =
  'Bạn đang tự bỏ vai trò Quản trị hệ thống của chính mình — sau khi lưu bạn sẽ mất ' +
  'quyền quản trị, muốn lấy lại phải nhờ quản trị khác. Tiếp tục?'

function httpError(status: number, message: string) {
  return Object.assign(new Error(message), {
    response: { status, data: { success: false, error: { code: String(status), message } } },
  })
}

beforeEach(() => {
  currentUserId = 99
  currentRoleIds = []
  toastError.mockReset()
  confirmMock.mockReset()
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

    const { queryClient } = build()
    const oDeptHead = await screen.findByRole('checkbox', { name: /Trưởng phòng/ })

    await nguoi.click(oDeptHead)
    expect(oDeptHead).toBeChecked()

    //  Đúng nhịp hỏng: bản ghi đổi ở máy chủ trong lúc người dùng đang tick dở.
    khoa = true
    await queryClient.refetchQueries({ queryKey: ['hr', 'users', 31] })

    expect(oDeptHead).toBeChecked()

    await nguoi.click(screen.getByRole('button', { name: /Lưu vai trò/ }))
    expect(httpPut).toHaveBeenCalledWith('/api/users/31/roles', { role_ids: [2, 3] }, SILENT)
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

    const { queryClient } = build()
    const oAdmin = await screen.findByRole('checkbox', { name: /Quản trị hệ thống/ })
    expect(oAdmin).not.toBeChecked()

    roleIds = [1, 2]
    await queryClient.refetchQueries({ queryKey: ['hr', 'users', 31] })

    expect(await screen.findByRole('checkbox', { name: /Quản trị hệ thống/ })).toBeChecked()
  })

  it('vào lại trang khi bộ đệm còn nóng thì dấu tick vẫn đúng', async () => {
    //  Đại ca báo 25/09/2026: mở trang thấy tick đủ, quay ra trang trước rồi vào
    //  lại thì mọi dấu tick biến mất, phải tải lại cả trang mới hiện ra.
    //
    //  Lần vào thứ hai React Query trả dữ liệu từ bộ đệm NGAY ở lượt render đầu.
    //  Bản cũ chép `account.role_ids` vào state và chỉ chép khi dữ liệu «đổi so
    //  với lượt render trước», mà ở lượt render ĐẦU TIÊN thì không có gì đổi cả
    //  — nên state đứng nguyên ở rỗng. Lần vào đầu tiên không lộ vì lúc đó dữ
    //  liệu chưa có, phải chờ tải xong, và chính cú «chưa có -> có» là nhịp chép.
    apiGet.mockImplementation((url: string) =>
      url === '/api/users/31' ? Promise.resolve(account([2])) : Promise.resolve(ROLES),
    )

    const queryClient = newQueryClient()
    const lanDau = build(queryClient)
    expect(await screen.findByRole('checkbox', { name: /Nhân sự/ })).toBeChecked()

    lanDau.unmount()
    build(queryClient)

    expect(await screen.findByRole('checkbox', { name: /Nhân sự/ })).toBeChecked()
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

  it('quản trị hệ thống mở trang của chính mình thì sửa được', async () => {
    //  bao-CR-523: backend miễn chốt hai người cho người giữ `admin`.
    currentUserId = 31
    currentRoleIds = [1, 2]
    apiGet.mockImplementation((url: string) =>
      url === '/api/users/31' ? Promise.resolve(account([1, 2])) : Promise.resolve(ROLES),
    )

    build()

    expect(await screen.findByRole('checkbox', { name: /Trưởng phòng/ })).toBeEnabled()
    expect(screen.getByRole('button', { name: /Lưu vai trò/ })).toBeEnabled()
    expect(screen.queryByText(/chốt hai người/)).not.toBeInTheDocument()
  })

  it('tự bỏ vai trò Quản trị: 409 thì hỏi lại, đồng ý thì gửi lại kèm cờ', async () => {
    const nguoi = userEvent.setup()
    currentUserId = 31
    currentRoleIds = [1, 2]
    apiGet.mockImplementation((url: string) =>
      url === '/api/users/31' ? Promise.resolve(account([1, 2])) : Promise.resolve(ROLES),
    )
    httpPut
      .mockRejectedValueOnce(httpError(409, SELF_ADMIN_QUESTION))
      .mockResolvedValueOnce({ data: { success: true, message: 'Đã gán vai trò', data: null } })
    confirmMock.mockResolvedValue(true)

    build()
    await nguoi.click(await screen.findByRole('checkbox', { name: /Quản trị hệ thống/ }))
    await nguoi.click(screen.getByRole('button', { name: /Lưu vai trò/ }))

    await vi.waitFor(() => expect(httpPut).toHaveBeenCalledTimes(2))
    //  Câu hỏi lấy NGUYÊN từ backend; 409 là câu hỏi nên không bắn toast đỏ.
    expect(confirmMock).toHaveBeenCalledWith(expect.objectContaining({ message: SELF_ADMIN_QUESTION }))
    expect(toastError).not.toHaveBeenCalled()
    expect(httpPut).toHaveBeenNthCalledWith(1, '/api/users/31/roles', { role_ids: [2] }, SILENT)
    expect(httpPut).toHaveBeenNthCalledWith(
      2,
      '/api/users/31/roles',
      { role_ids: [2], confirm_self_admin_removal: true },
      SILENT,
    )
  })

  it('tự bỏ vai trò Quản trị mà bấm Hủy thì không gửi lại', async () => {
    const nguoi = userEvent.setup()
    currentUserId = 31
    currentRoleIds = [1, 2]
    apiGet.mockImplementation((url: string) =>
      url === '/api/users/31' ? Promise.resolve(account([1, 2])) : Promise.resolve(ROLES),
    )
    httpPut.mockRejectedValueOnce(httpError(409, SELF_ADMIN_QUESTION))
    confirmMock.mockResolvedValue(false)

    build()
    const oAdmin = await screen.findByRole('checkbox', { name: /Quản trị hệ thống/ })
    await nguoi.click(oAdmin)
    await nguoi.click(screen.getByRole('button', { name: /Lưu vai trò/ }))

    await vi.waitFor(() => expect(confirmMock).toHaveBeenCalledTimes(1))
    expect(httpPut).toHaveBeenCalledTimes(1)
    //  Nháp vẫn giữ nguyên để người dùng đổi ý tiếp.
    expect(oAdmin).not.toBeChecked()
  })

  it('400 «phải còn ít nhất một quản trị» thì báo lỗi, không hỏi xác nhận', async () => {
    const nguoi = userEvent.setup()
    currentUserId = 31
    currentRoleIds = [1, 2]
    apiGet.mockImplementation((url: string) =>
      url === '/api/users/31' ? Promise.resolve(account([1, 2])) : Promise.resolve(ROLES),
    )
    httpPut.mockRejectedValueOnce(
      httpError(400, 'Hệ thống phải còn ít nhất một quản trị đang hoạt động'),
    )

    build()
    await nguoi.click(await screen.findByRole('checkbox', { name: /Quản trị hệ thống/ }))
    await nguoi.click(screen.getByRole('button', { name: /Lưu vai trò/ }))

    await vi.waitFor(() =>
      expect(toastError).toHaveBeenCalledWith('Hệ thống phải còn ít nhất một quản trị đang hoạt động'),
    )
    expect(confirmMock).not.toHaveBeenCalled()
    expect(httpPut).toHaveBeenCalledTimes(1)
  })
})
