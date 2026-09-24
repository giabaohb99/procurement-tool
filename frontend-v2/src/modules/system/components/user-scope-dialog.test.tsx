import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { PermissionMap } from '@/core/authorization/permission-types'
import { UserScopeDialog } from './user-scope-dialog'

/**
 * Hộp thoại PHẠM VI DỮ LIỆU của cặp (tài khoản × vai trò) — màn khai quyền.
 *
 * Vì sao đáng kiểm kỹ hơn một hộp thoại thường: đây là kiểu hỏng thứ tư của
 * giao diện phân quyền — *khai sai*. Ba kiểu kia (nút giả, giấu nhầm, rỗng mập
 * mờ) chỉ làm phiền người dùng; kiểu này GHI SAI xuống cơ sở dữ liệu thứ mà
 * người quản trị vừa tick, rồi backend chạy hoàn toàn đúng trên dữ liệu sai đó.
 * Không có triệu chứng nào cả.
 */

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

//  Bản đồ quyền của người ĐANG khai quyền cho người khác (không phải của tài
//  khoản đang được sửa). Ba danh mục trong hộp thoại thuộc ba khóa khác nhau.
let permissions: PermissionMap = {
  company: { read: true },
  department: { read: true },
  employee: { read: true },
}

vi.mock('@/core/auth/auth-store', () => ({
  useAuthStore: (selector: (state: { user: { permissions: PermissionMap } | null }) => unknown) =>
    selector({ user: { permissions } }),
}))

const COMPANIES = [
  { id: 1, code: 'DEGO', name: 'Công ty CP DEGO Holding' },
  { id: 2, code: 'DGF', name: 'Công ty CP DEGO Food' },
]

/** Hai phòng TRÙNG TÊN ở hai pháp nhân — đúng hình dạng gây ra lỗ 09-A. */
const DEPARTMENTS_TRUNG_TEN = [
  { id: 10, code: 'KT-DEGO', name: 'Phòng Kế toán', company_id: 1 },
  { id: 20, code: 'KT-DGF', name: 'Phòng Kế toán', company_id: 2 },
]

const DEPARTMENTS = [
  { id: 10, code: 'KT', name: 'Phòng Kế toán', company_id: 1 },
  { id: 11, code: 'HC', name: 'Phòng Hành chính', company_id: 1 },
]

const EMPLOYEES = [
  { id: 5, code: 'NV005', full_name: 'Trần Văn Nam' },
  { id: 6, code: 'NV006', full_name: 'Lê Thị Hoa' },
]

/**
 * Hồ sơ nhân sự của CHỦ tài khoản đang được khai phạm vi (khác ba người trong
 * danh bạ ở trên). Đây là nguồn của công ty / phòng ban MẶC ĐỊNH — thứ
 * `_role_scope_cond` đọc, và là thứ khối tóm tắt phải in ra bằng tên thật.
 */
const HO_SO_CHU_TAI_KHOAN = {
  id: 12,
  code: 'NV012',
  full_name: 'Nguyễn Văn Chủ',
  company_id: 1,
  company_name: 'Công ty CP DEGO Holding',
  department_id: 11,
  department_name: 'Phòng Hành chính',
}

/** Meta của backend — bậc xếp từ hẹp tới rộng, y như `SCOPES` của `core/permissions.py`. */
const META = {
  entities: [
    { key: 'purchase_request', label: 'Yêu cầu mua hàng' },
    { key: 'purchase_order', label: 'Đơn mua hàng' },
    { key: 'supplier', label: 'Nhà cung cấp' },
  ],
  actions: [{ key: 'read', label: 'Xem' }],
  scopes: [
    { key: 'own', label: 'Của mình' },
    { key: 'assigned', label: 'Được giao' },
    { key: 'dept_proc', label: 'Được giao + đã duyệt trong phòng' },
    { key: 'dept', label: 'Phòng ban mình' },
    { key: 'company', label: 'Công ty mình' },
    { key: 'all', label: 'Tất cả' },
  ],
}

/** Ma trận của một nhân viên thu mua nhà máy — đúng hình dạng bao-CR-414. */
const MA_TRAN_NHA_MAY = [
  { entity: 'purchase_request', scope: 'assigned', can_read: true },
  { entity: 'purchase_order', scope: 'dept_proc', can_read: true },
  { entity: 'supplier', scope: 'all', can_read: true },
]

interface RouteData {
  companies?: unknown[]
  departments?: unknown[]
  employees?: unknown[]
  /** Phạm vi đã lưu, tra theo `roleId`. */
  scopes?: Record<number, Record<string, unknown>>
  /** Ma trận quyền của vai trò = TẦNG 1 của phạm vi. */
  rolePermissions?: unknown[]
  /** Hồ sơ nhân sự của chủ tài khoản; `null` = cửa `/api/employees/{id}` trả 403. */
  owner?: Record<string, unknown> | null
  /** Phòng KIÊM NHIỆM của chủ tài khoản (id), cửa `/api/employees/{id}/departments`. */
  extraDepartmentIds?: number[]
}

/**
 * `/api/employees/{id}/departments` — KHÔNG được so bằng `endsWith('/departments')`
 * suông: cửa danh mục `/api/departments` cũng kết thúc y hệt (bài A13 từng đếm
 * nhầm nó).
 */
function isOwnerDepartmentsUrl(url: string) {
  return url.startsWith('/api/employees/') && url.endsWith('/departments')
}

function mockRoutes(data: RouteData = {}) {
  apiGet.mockImplementation((url: string) => {
    if (url.includes('/scope')) {
      const roleId = Number(url.match(/roles\/(\d+)\/scope/)?.[1] ?? 0)
      return Promise.resolve(data.scopes?.[roleId] ?? {})
    }
    if (url === '/api/roles/meta') return Promise.resolve(META)
    if (url.endsWith('/permissions')) {
      return Promise.resolve(data.rolePermissions ?? MA_TRAN_NHA_MAY)
    }
    if (url === '/api/companies') {
      return Promise.resolve({ total: 0, items: data.companies ?? COMPANIES })
    }
    if (url === '/api/departments') {
      return Promise.resolve({ total: 0, items: data.departments ?? DEPARTMENTS })
    }
    if (url === '/api/employees') {
      return Promise.resolve({ total: 0, items: data.employees ?? EMPLOYEES })
    }
    //  Phòng chính + kiêm nhiệm của chủ tài khoản (bao-CR-430) — phải đứng TRƯỚC
    //  nhánh hồ sơ bên dưới, vì nhánh đó bắt mọi đường con của `/api/employees/`.
    if (isOwnerDepartmentsUrl(url)) {
      if (data.owner === null) return Promise.reject(new Error('403'))
      return Promise.resolve({
        primary_department_id: 11,
        extra_department_ids: data.extraDepartmentIds ?? [],
      })
    }
    //  Hồ sơ của CHỦ tài khoản — cửa `/{id}`, khác hẳn cửa danh bạ ở trên.
    if (url.startsWith('/api/employees/')) {
      if (data.owner === null) return Promise.reject(new Error('403'))
      return Promise.resolve(data.owner ?? HO_SO_CHU_TAI_KHOAN)
    }
    return Promise.reject(new Error(`URL không được khai trong test: ${url}`))
  })
}

function build(props: Partial<Parameters<typeof UserScopeDialog>[0]> = {}) {
  const onClose = vi.fn()
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  const view = render(
    //  `MemoryRouter`: khối tóm tắt có đường dẫn sang màn Ma trận quyền.
    <MemoryRouter>
      <QueryClientProvider client={client}>
        <UserScopeDialog
          userId={31}
          employeeId={12}
          roleId={7}
          roleName="Kế toán"
          onClose={onClose}
          {...props}
        />
      </QueryClientProvider>
    </MemoryRouter>,
  )
  return { ...view, onClose, client }
}

/**
 * Mở mục «Ngoại lệ» — MẶC ĐỊNH ĐÓNG từ 19/09/2026 (đại ca chốt gộp hai tầng).
 *
 * `Collapsible` của Radix HỦY MOUNT phần thân khi đóng, nên mọi chip công ty /
 * phòng ban / nhân sự đều không có trong DOM cho tới khi bấm nút này. Bài kiểm
 * nào đụng tới chip thì phải gọi nó trước.
 */
async function openExceptions(user: ReturnType<typeof userEvent.setup>) {
  await user.click(await screen.findByRole('button', { name: /^Ngoại lệ/ }))
}

beforeEach(() => {
  //  `restoreMocks` của vitest.config chỉ khôi phục spy, không xóa lịch sử gọi
  //  của `vi.fn()` khai ở tầng module -> phải tự dọn, kẻo bài sau đếm cả lượt
  //  gọi của bài trước.
  apiGet.mockReset()
  httpPut.mockReset()
  permissions = { company: { read: true }, department: { read: true }, employee: { read: true } }
  httpPut.mockResolvedValue({ data: { success: true, data: null } })
  mockRoutes()
})

describe('A1 — lưu đúng thứ vừa tick', () => {
  it('tick một chip công ty rồi Lưu thì PUT đi đúng mảng đó', async () => {
    const user = userEvent.setup()
    build()

    await openExceptions(user)
    await user.click(await screen.findByRole('button', { name: 'DEGO' }))
    await user.click(screen.getByRole('button', { name: 'Lưu phạm vi' }))

    await waitFor(() => expect(httpPut).toHaveBeenCalled())
    const [url, body] = httpPut.mock.calls[0] as [string, Record<string, unknown>]
    expect(url).toBe('/api/users/31/roles/7/scope')
    expect(body.companies).toEqual([1])
    //  Các chiều KHÔNG đụng tới phải đi rỗng, không được biến mất khỏi payload:
    //  backend đọc thiếu khóa là giữ nguyên giá trị cũ ở chiều đó.
    expect(body.departments).toEqual([])
    expect(body.exclude_departments).toEqual([])
    expect(body.employees).toEqual([])
  })

  it('tick lần hai thì BỎ chọn, không thêm trùng', async () => {
    const user = userEvent.setup()
    build()

    await openExceptions(user)
    const chip = await screen.findByRole('button', { name: 'DEGO' })
    await user.click(chip)
    await user.click(chip)
    await user.click(screen.getByRole('button', { name: 'Lưu phạm vi' }))

    await waitFor(() => expect(httpPut).toHaveBeenCalled())
    expect((httpPut.mock.calls[0][1] as Record<string, unknown>).companies).toEqual([])
  })
})

describe('A2 — hai phòng TRÙNG TÊN ở hai pháp nhân (lỗ 09-A)', () => {
  //  ⚠️ BÀI KIỂM NÀY CỐ Ý ĐANG ĐỎ — `it.fails` giữ suite xanh nhưng sẽ đổi
  //  màu ngay ngày ai đó sửa 09-A, và lúc đó phải đổi `it.fails` thành `it`.
  //
  //  Hộp thoại định danh phòng ban bằng TÊN (`scope.departments.includes(name)`),
  //  mà nó nạp phòng của MỌI pháp nhân và không hiện pháp nhân bên cạnh tên. Hệ
  //  có 11 pháp nhân, tên phòng đặt theo khuôn ("Phòng Kế toán", "Phòng Hành
  //  chính") nên trùng tên là chuyện KHI NÀO chứ không phải CÓ HAY KHÔNG.
  //  Sửa được nó phải đổi cả `ScopeUpdate`/`set_user_scope` của backend và vẫn
  //  phải nhận kiểu chuỗi cũ cho bản `frontend/` đã đóng băng -> việc riêng.
  it.fails('tick một chip thì chip kia KHÔNG được sáng theo', async () => {
    const user = userEvent.setup()
    mockRoutes({ departments: DEPARTMENTS_TRUNG_TEN })
    build()

    await openExceptions(user)
    const trung = await screen.findAllByRole('button', { name: 'Phòng Kế toán' })
    //  Bốn chip: hai ở "Phòng ban được xem", hai ở "Loại trừ phòng ban".
    expect(trung).toHaveLength(4)

    await user.click(trung[0])
    expect(trung[0]).toHaveAttribute('aria-pressed', 'true')
    expect(trung[1]).toHaveAttribute('aria-pressed', 'false')
  })

  it('và lưu xuống chỉ còn MỘT chuỗi tên — không phân biệt được hai phòng', async () => {
    //  Chiều còn lại của cùng một lỗ, ghi lại để khỏi ai tưởng đã vá xong khi
    //  mới sửa phần hiển thị: payload gửi đi là `['Phòng Kế toán']`, backend
    //  không có cách nào biết là phòng của pháp nhân nào.
    const user = userEvent.setup()
    mockRoutes({ departments: DEPARTMENTS_TRUNG_TEN })
    build()

    await openExceptions(user)
    const trung = await screen.findAllByRole('button', { name: 'Phòng Kế toán' })
    await user.click(trung[0])
    await user.click(screen.getByRole('button', { name: 'Lưu phạm vi' }))

    await waitFor(() => expect(httpPut).toHaveBeenCalled())
    expect((httpPut.mock.calls[0][1] as Record<string, unknown>).departments).toEqual([
      'Phòng Kế toán',
    ])
  })
})

describe('A3 — mảng rỗng nghĩa là KHÔNG GIỚI HẠN', () => {
  it('màn hình nói ra điều đó, không để người khai tự đoán', async () => {
    const user = userEvent.setup()
    build()
    await openExceptions(user)
    //  "Để trống = không thấy gì" là cách hiểu tự nhiên và ngược hẳn sự thật.
    expect(
      screen.getByText(/Để trống một mục = không giới hạn chiều đó/),
    ).toBeInTheDocument()
  })

  it('không tick gì mà Lưu thì gửi mảng rỗng, không gửi cả danh mục', async () => {
    const user = userEvent.setup()
    build()
    //  Chờ phạm vi nạp xong: nút Lưu bị khóa suốt lúc `isLoading`, bấm sớm là
    //  bài kiểm xanh giả vì chẳng có request nào đi cả.
    await screen.findByRole('button', { name: /^Ngoại lệ/ })
    await user.click(screen.getByRole('button', { name: 'Lưu phạm vi' }))

    await waitFor(() => expect(httpPut).toHaveBeenCalled())
    expect(httpPut.mock.calls[0][1]).toEqual({
      companies: [],
      departments: [],
      employees: [],
      exclude_companies: [],
      exclude_departments: [],
      exclude_employees: [],
    })
  })
})

describe('A4 — đổi vai trò thì nạp lại phạm vi của vai trò đó', () => {
  it('không giữ state của vai trò mở trước đó', async () => {
    mockRoutes({
      scopes: {
        7: { companies: [1], departments: [], employees: [], exclude_companies: [], exclude_departments: [], exclude_employees: [] },
        8: { companies: [2], departments: [], employees: [], exclude_companies: [], exclude_departments: [], exclude_employees: [] },
      },
    })
    const user = userEvent.setup()
    const { rerender, client } = build({ roleId: 7 })

    await openExceptions(user)
    await waitFor(() =>
      expect(screen.getByRole('button', { name: 'DEGO' })).toHaveAttribute('aria-pressed', 'true'),
    )

    rerender(
      <MemoryRouter>
        <QueryClientProvider client={client}>
          <UserScopeDialog
            userId={31}
            employeeId={12}
            roleId={8}
            roleName="Thu mua"
            onClose={vi.fn()}
          />
        </QueryClientProvider>
      </MemoryRouter>,
    )
    //  Giữ nguyên `MemoryRouter` ở gốc để React GIỮ đúng một instance hộp thoại —
    //  đổi kiểu thẻ gốc là remount, và remount thì state nào cũng sạch, bài kiểm
    //  thành xanh giả. Mục «Ngoại lệ» vì thế vẫn đang mở.

    await waitFor(() =>
      expect(screen.getByRole('button', { name: 'DGF' })).toHaveAttribute('aria-pressed', 'true'),
    )
    //  Chip của vai trò cũ phải TẮT. Giữ lại là lưu nhầm phạm vi vai trò này
    //  sang vai trò kia mà không ai thấy gì bất thường.
    expect(screen.getByRole('button', { name: 'DEGO' })).toHaveAttribute('aria-pressed', 'false')
  })
})

describe('A5 — cùng một phòng vừa được xem thêm vừa bị loại trừ', () => {
  it('vẫn tick được cả hai, nhưng màn hình nói ra là loại trừ THẮNG', async () => {
    //  Backend xử "loại trừ thắng" (`_explicit_cond` nối bằng `and_` sau phần
    //  cộng thêm), nên tick cả hai = mở xong tự bịt lại. Tới 19/09/2026 hộp thoại
    //  im lặng ở đúng chỗ này; giờ phải cảnh báo tại chỗ, còn việc GHI vẫn để
    //  nguyên ý người khai — cảnh báo, không tự sửa dữ liệu của người ta.
    const user = userEvent.setup()
    build()

    await openExceptions(user)
    const chipsKeToan = await screen.findAllByRole('button', { name: 'Phòng Kế toán' })
    expect(chipsKeToan).toHaveLength(2) // 1 ở "xem thêm", 1 ở "loại trừ"
    await user.click(chipsKeToan[0])
    await user.click(chipsKeToan[1])

    expect(screen.getByText(/Loại trừ thắng/)).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Lưu phạm vi' }))

    await waitFor(() => expect(httpPut).toHaveBeenCalled())
    const body = httpPut.mock.calls[0][1] as Record<string, unknown>
    expect(body.departments).toEqual(['Phòng Kế toán'])
    expect(body.exclude_departments).toEqual(['Phòng Kế toán'])
  })

  it('chỉ tick một bên thì KHÔNG cảnh báo — báo động giả còn hại hơn im lặng', async () => {
    const user = userEvent.setup()
    build()

    await openExceptions(user)
    const chipsKeToan = await screen.findAllByRole('button', { name: 'Phòng Kế toán' })
    await user.click(chipsKeToan[1])

    expect(screen.queryByText(/Loại trừ thắng/)).toBeNull()
  })
})

describe('A6 — ba danh mục có cổng quyền (09-D)', () => {
  it('thiếu employee.read thì KHÔNG gọi /api/employees', async () => {
    const user = userEvent.setup()
    permissions = { company: { read: true }, department: { read: true } }
    build()

    await openExceptions(user)
    await screen.findByRole('button', { name: 'DEGO' })
    const urls = apiGet.mock.calls.map((c) => c[0])
    expect(urls).not.toContain('/api/employees')
    //  Kể cả cửa hồ sơ của chủ tài khoản — cùng một khóa quyền, cùng một cú 403.
    expect(urls.some((url: string) => url.startsWith('/api/employees'))).toBe(false)
    expect(urls).toContain('/api/companies')
  })

  it('thiếu quyền thì nói ra, không để một ô rỗng', async () => {
    //  403 trên GET KHÔNG bật toast (`core/api/http-client.ts`), nên ô rỗng là
    //  tất cả những gì người khai quyền nhìn thấy — và họ đọc ra thành "công ty
    //  này chưa khai phòng ban nào" rồi khai phạm vi hụt.
    const user = userEvent.setup()
    permissions = { company: { read: true } }
    build()

    await openExceptions(user)
    await screen.findByRole('button', { name: 'DEGO' })
    expect(
      screen.getAllByText(/Bạn không có quyền xem danh mục phòng ban/).length,
    ).toBeGreaterThan(0)
    expect(screen.getAllByText(/Bạn không có quyền xem danh bạ nhân sự/).length).toBe(2)
  })

  it('không có quyền nào thì hộp thoại vẫn mở được và không gọi danh mục nào', async () => {
    permissions = {}
    build()

    await waitFor(() => expect(apiGet).toHaveBeenCalled())
    const urls = apiGet.mock.calls.map((c) => c[0])
    expect(urls).toEqual(['/api/users/31/roles/7/scope'])
  })
})

describe('A7 — danh mục rỗng', () => {
  it('nói "chưa có … nào trong danh mục", khác hẳn câu thiếu quyền', async () => {
    //  Đủ quyền ở CẢ BỐN danh mục (kể cả `role.read` của khối tóm tắt) để chữ
    //  "không có quyền" trên màn chỉ có thể tới từ chỗ đang kiểm.
    const user = userEvent.setup()
    permissions = {
      company: { read: true },
      department: { read: true },
      employee: { read: true },
      role: { read: true },
    }
    mockRoutes({ companies: [], departments: [] })
    build()

    await openExceptions(user)
    await waitFor(() => expect(screen.getByText(/Chưa có công ty nào/)).toBeInTheDocument())
    expect(screen.getAllByText(/Chưa có phòng ban nào/).length).toBe(2)
    expect(screen.queryByText(/không có quyền/i)).toBeNull()
  })
})

describe('A8 — danh bạ 2000 người', () => {
  it('không dựng 2000 chip; phải gõ mới ra kết quả và cắt ở 40 dòng', async () => {
    const user = userEvent.setup()
    const many = Array.from({ length: 2000 }, (_, i) => ({
      id: i + 1,
      code: `NV${String(i + 1).padStart(4, '0')}`,
      full_name: `Nhân sự ${i + 1}`,
    }))
    mockRoutes({ employees: many })
    build()

    await openExceptions(user)
    await screen.findByRole('button', { name: 'DEGO' })
    //  Mặc định ở trạng thái "không giới hạn": không một chip nhân sự nào.
    expect(screen.queryByRole('button', { name: /NV0001/ })).toBeNull()

    await user.click(screen.getAllByRole('button', { name: 'Tùy chỉnh' })[0])
    await user.type(screen.getByPlaceholderText(/Gõ mã \/ tên để tìm nhân sự/), 'Nhân sự 1')

    //  40 là trần cứng trong `ScopeEmployeePicker`. Không có trần thì gõ một ký
    //  tự là dựng vài nghìn nút, hộp thoại đứng hình.
    await waitFor(() => {
      expect(screen.getAllByRole('button', { name: /Nhân sự 1/ }).length).toBe(40)
    })
  })
})

describe('A9 — lưu hỏng', () => {
  it('hộp thoại KHÔNG đóng và giữ nguyên thứ vừa tick', async () => {
    const user = userEvent.setup()
    httpPut.mockRejectedValue(new Error('403'))
    const { onClose } = build()

    await openExceptions(user)
    await user.click(await screen.findByRole('button', { name: 'DEGO' }))
    await user.click(screen.getByRole('button', { name: 'Lưu phạm vi' }))

    await waitFor(() => expect(httpPut).toHaveBeenCalled())
    //  Đóng hộp khi lưu hỏng = người dùng tưởng đã lưu xong, và mọi ô vừa tick
    //  biến mất. Hai cái sai cộng lại thành khai quyền sai mà không ai biết.
    expect(onClose).not.toHaveBeenCalled()
    expect(screen.getByRole('button', { name: 'DEGO' })).toHaveAttribute('aria-pressed', 'true')
  })

  it('lưu được thì mới đóng', async () => {
    const user = userEvent.setup()
    const { onClose } = build()

    await screen.findByRole('button', { name: /^Ngoại lệ/ })
    await user.click(screen.getByRole('button', { name: 'Lưu phạm vi' }))

    await waitFor(() => expect(onClose).toHaveBeenCalledTimes(1))
  })
})

describe('A11 — MỘT khối trả lời "tài khoản này thấy gì"', () => {
  //  Lý do cả cụm này tồn tại: phạm vi có hai tầng ở hai màn khác nhau, và hộp
  //  thoại cũ chỉ bày tầng 2 nên không màn nào trả lời được câu duy nhất người
  //  khai cần. Đại ca bác thẳng bản hai khối ngày 19/09/2026 — "viết dài quá đâu
  //  ai hiểu đâu, vậy thì 2 tầng thành 1 rồi" — nên nay chỉ còn MỘT khối, và nó
  //  phải nói bằng TÊN THẬT lấy từ hồ sơ của chủ tài khoản.
  beforeEach(() => {
    permissions = {
      company: { read: true },
      department: { read: true },
      employee: { read: true },
      role: { read: true },
    }
  })

  it('nói bậc của từng nhóm chứng từ bằng lời thường, không bằng tên bậc suông', async () => {
    build()

    await screen.findByText('Đơn mua hàng')
    expect(screen.getByText('Yêu cầu mua hàng')).toBeInTheDocument()
    //  Nhãn bậc ("Được giao + đã duyệt trong phòng") cố ý KHÔNG in ra: đó là từ của người
    //  dựng hệ thống. Câu giải thích mới là thứ người khai đọc.
    expect(screen.getByText(/nhờ phòng này mua giúp/)).toBeInTheDocument()
    expect(screen.getByText(/được giao cho họ xử lý/)).toBeInTheDocument()
  })

  it('thay TÊN THẬT của công ty / phòng ban trong hồ sơ vào câu tóm tắt', async () => {
    //  Chính là điều đại ca chỉ ra: "tài khoản thuộc công ty ABA thì mặc định
    //  phạm vi của nó là ABA". Câu "công ty của người này" đúng nhưng người đọc
    //  vẫn phải đi tra, tức là màn hình đẩy việc ngược lại cho họ.
    mockRoutes({
      rolePermissions: [
        { entity: 'supplier', scope: 'company', can_read: true },
        { entity: 'purchase_order', scope: 'dept', can_read: true },
      ],
    })
    build()

    await waitFor(() =>
      expect(
        screen.getByText(/mọi chứng từ trong công ty Công ty CP DEGO Holding/),
      ).toBeInTheDocument(),
    )
    expect(screen.getByText(/mọi chứng từ của phòng Phòng Hành chính/)).toBeInTheDocument()
  })

  it('tài khoản CHƯA GẮN hồ sơ nhân sự thì cảnh báo là không thấy gì hết', async () => {
    //  `_role_scope_cond` trả `false()` khi `company_id = 0`, nên đây không phải
    //  "lọc hụt" mà là chặn sạch. Không nói ra thì người khai đi tick bù ở mục
    //  Ngoại lệ — sai chỗ, và vẫn không thấy gì.
    mockRoutes({ rolePermissions: [{ entity: 'supplier', scope: 'company', can_read: true }] })
    build({ employeeId: 0 })

    await waitFor(() =>
      expect(screen.getByText(/Tài khoản chưa gắn hồ sơ nhân sự/)).toBeInTheDocument(),
    )
    expect(screen.getByText(/không thấy một chứng từ nào/)).toBeInTheDocument()
  })

  it('hồ sơ có nhưng CHƯA GẮN công ty thì cảnh báo đúng chỗ phải đi sửa', async () => {
    //  Khác hẳn ca trên: hồ sơ tồn tại, thiếu là thiếu ô công ty trong hồ sơ —
    //  nên việc phải làm nằm ở màn Nhân sự, không nằm ở hộp thoại này.
    mockRoutes({
      rolePermissions: [{ entity: 'supplier', scope: 'company', can_read: true }],
      owner: { ...HO_SO_CHU_TAI_KHOAN, company_id: 0, company_name: '' },
    })
    build()

    await waitFor(() =>
      expect(
        screen.getByText(/Hồ sơ nhân sự của tài khoản chưa gắn công ty/),
      ).toBeInTheDocument(),
    )
  })

  it('chưa đọc được hồ sơ thì nói là đang thiếu tên thật, KHÔNG vu là chưa gắn công ty', async () => {
    //  Ba trạng thái, đừng gộp hai cái sau: chưa gắn hồ sơ (biết chắc) · có hồ sơ
    //  mà đọc không ra (không biết gì) · đọc được và thấy trống. Gộp hai cái sau
    //  là màn hình khẳng định một điều nó không kiểm chứng được, rồi người khai
    //  đi sửa một hồ sơ vốn chẳng sai gì.
    mockRoutes({
      rolePermissions: [{ entity: 'supplier', scope: 'company', can_read: true }],
      owner: null,
    })
    build()

    await waitFor(() =>
      expect(screen.getByText(/Chưa đọc được hồ sơ nhân sự của tài khoản/)).toBeInTheDocument(),
    )
    expect(screen.queryByText(/chưa gắn công ty/)).toBeNull()
  })

  it('có đường sang đúng vai trò ở màn Ma trận quyền, không bắt tự tìm lại', async () => {
    build()

    const link = await screen.findByRole('link', { name: /Sửa bậc ở màn Ma trận quyền/ })
    expect(link).toHaveAttribute('href', '/system/permissions?role=7')
  })

  it('thiếu role.read thì nói ra và KHÔNG gọi API vai trò', async () => {
    //  403 trên GET không bật toast, nên không gác là người khai thấy một khung
    //  trống rồi tưởng vai trò này chưa được cấp quyền gì.
    const user = userEvent.setup()
    permissions = { company: { read: true }, department: { read: true } }
    build()

    await openExceptions(user)
    await screen.findByRole('button', { name: 'DEGO' })
    const urls = apiGet.mock.calls.map((c) => c[0])
    expect(urls).not.toContain('/api/roles/meta')
    expect(urls.some((url: string) => url.endsWith('/permissions'))).toBe(false)
    expect(screen.getByText(/không có quyền xem vai trò/)).toBeInTheDocument()
  })

  it('vai trò chưa tick ô XEM nào thì cảnh báo — gán xong vẫn không thấy gì', async () => {
    //  Trường hợp thật hay gặp: tạo vai trò mới, gán cho người ta, quên vào ma
    //  trận tick quyền. Không có câu này thì hộp thoại bày mục Ngoại lệ cho một
    //  vai trò rỗng tuếch, và người khai đi tick bù ở đó.
    mockRoutes({ rolePermissions: [{ entity: 'purchase_order', scope: 'dept', can_read: false }] })
    build()

    await waitFor(() =>
      expect(screen.getByText(/chưa được tick quyền XEM ở đối tượng nào/)).toBeInTheDocument(),
    )
  })

  it('bậc toàn «Tất cả» thì nói thẳng ô xem thêm phòng ban không đổi được gì', async () => {
    //  `scope_condition` bỏ qua phần cộng thêm khi bậc vai trò đã thấy hết. Không
    //  nói ra thì người khai tick cả buổi mà không có gì thay đổi, rồi kết luận
    //  là hệ hỏng.
    const user = userEvent.setup()
    mockRoutes({ rolePermissions: [{ entity: 'supplier', scope: 'all', can_read: true }] })
    build()

    await openExceptions(user)
    await waitFor(() =>
      expect(screen.getByText(/đã ở bậc «Tất cả» nên cộng thêm phòng ban/)).toBeInTheDocument(),
    )
  })
})

describe('A12 — NGOẠI LỆ gấp lại, nhưng không được giấu', () => {
  it('chưa khai ngoại lệ nào thì nhãn không đeo số và không có mục nào trong khối tóm tắt', async () => {
    build()

    const nut = await screen.findByRole('button', { name: /^Ngoại lệ/ })
    //  Có số trên nhãn khi chưa khai gì = dọa người khai mở ra xem một mục rỗng.
    expect(nut).toHaveTextContent('Ngoại lệ')
    expect(nut.textContent).not.toMatch(/\d/)
    expect(screen.queryByText(/Ngoại lệ đang khai cho riêng tài khoản này/)).toBeNull()
  })

  it('mặc định ĐÓNG — mở hộp thoại ra là không thấy ô tick nào', async () => {
    //  Đại ca bác đúng chỗ này: bày sẵn năm ô tick thì ai mở hộp thoại cũng tưởng
    //  mình phải khai, trong khi gán vai trò xong là tài khoản đã có phạm vi.
    build()

    await screen.findByRole('button', { name: /^Ngoại lệ/ })
    expect(screen.queryByRole('button', { name: 'DEGO' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Phòng Kế toán' })).toBeNull()
  })

  it('gọi ô phòng ban là CỘNG THÊM, đúng chiều của backend', async () => {
    //  Đây là chỗ hiểu nhầm đắt nhất của màn này: tên cũ «Phòng ban được xem» đọc
    //  ra thành "chỉ thấy phòng này", trong khi `scope_condition` ghép nó bằng
    //  `or_` — tức là MỞ RỘNG. Khai nhầm chiều thì tài khoản thấy NHIỀU hơn ý
    //  người khai, và không có triệu chứng nào.
    const user = userEvent.setup()
    build()

    await openExceptions(user)
    const chips = await screen.findAllByRole('button', { name: 'Phòng Kế toán' })
    await user.click(chips[0])

    expect(screen.getByText(/Xem THÊM chứng từ của phòng Phòng Kế toán/)).toBeInTheDocument()
  })

  it('đổi câu tóm tắt ngay khi tick, không đợi bấm Lưu', async () => {
    const user = userEvent.setup()
    build()

    await openExceptions(user)
    await user.click(await screen.findByRole('button', { name: 'DEGO' }))
    expect(screen.getByText(/Chỉ trong công ty DEGO/)).toBeInTheDocument()

    //  Bỏ tick thì câu phải biến mất; giữ lại là nói dối người khai.
    await user.click(screen.getByRole('button', { name: 'DEGO' }))
    expect(screen.queryByText(/Chỉ trong công ty DEGO/)).toBeNull()
  })

  it('nhắc ngoại lệ phiếu NHỜ khi loại trừ một phòng (bao-CR-414)', async () => {
    const user = userEvent.setup()
    build()

    await openExceptions(user)
    const chips = await screen.findAllByRole('button', { name: 'Phòng Hành chính' })
    await user.click(chips[1])

    expect(screen.getByText(/nhờ phòng mình mua giúp/)).toBeInTheDocument()
  })

  it('đếm TỪNG MỤC trên nhãn, không đếm số câu tóm tắt', async () => {
    //  `summarizeScopeLimits` gộp cả một chiều thành một câu, nên đếm theo câu thì
    //  tick phòng thứ hai xong con số đứng yên và người khai tưởng lần tick vừa
    //  rồi rơi mất.
    const user = userEvent.setup()
    build()

    await openExceptions(user)
    const phong = await screen.findAllByRole('button', { name: 'Phòng Kế toán' })
    await user.click(phong[0])
    expect(screen.getByRole('button', { name: /^Ngoại lệ/ })).toHaveTextContent('Ngoại lệ (1)')

    await user.click((await screen.findAllByRole('button', { name: 'Phòng Hành chính' }))[0])
    expect(screen.getByRole('button', { name: /^Ngoại lệ/ })).toHaveTextContent('Ngoại lệ (2)')
  })

  it('gấp mục lại thì ngoại lệ ĐANG CÓ vẫn hiện ở khối tóm tắt', async () => {
    //  Gấp mà không nhắc thì khối trên nói "thấy công ty ABA" trong khi thật ra
    //  còn một phòng bị loại trừ — nói dối bằng cách bỏ bớt.
    const user = userEvent.setup()
    build()

    await openExceptions(user)
    const chips = await screen.findAllByRole('button', { name: 'Phòng Kế toán' })
    await user.click(chips[1])

    await user.click(screen.getByRole('button', { name: /^Ngoại lệ/ })) // gấp lại
    await waitFor(() => expect(screen.queryByRole('button', { name: 'DEGO' })).toBeNull())
    expect(screen.getByText(/Ngoại lệ đang khai cho riêng tài khoản này/)).toBeInTheDocument()
    expect(screen.getByText(/Bỏ chứng từ của phòng Phòng Kế toán/)).toBeInTheDocument()
  })
})

describe('A13 — CẢNH BÁO (không chặn) khi loại trừ phòng của chính chủ tài khoản (bao-CR-430)', () => {
  //  Đại ca hỏi 19/09/2026: "tk của nhà máy, mà mình vào phạm vi loại trừ đúng nhà
  //  máy luôn thì như thế nào" — backend cho lưu, không có triệu chứng, và phiếu
  //  của chính phòng mình biến mất khỏi mọi vai trò. Chốt: "cảnh báo thôi, đừng chặn".
  const CANH_BAO = /là phòng của chính người này/

  it('nói ra ngay khi tick loại trừ đúng phòng CHÍNH của chủ tài khoản, và VẪN cho Lưu', async () => {
    const user = userEvent.setup()
    build()

    await openExceptions(user)
    expect(screen.queryByText(CANH_BAO)).toBeNull()

    //  chips[1] = chip ở ô LOẠI TRỪ (chips[0] là ô xem thêm); Hành chính = phòng
    //  chính của `HO_SO_CHU_TAI_KHOAN`.
    const chips = await screen.findAllByRole('button', { name: 'Phòng Hành chính' })
    await user.click(chips[1])

    expect(screen.getByText(/Phòng Hành chính là phòng của chính người này/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Lưu phạm vi' })).toBeEnabled()

    await user.click(screen.getByRole('button', { name: 'Lưu phạm vi' }))
    await waitFor(() => expect(httpPut).toHaveBeenCalled())
    expect((httpPut.mock.calls[0][1] as Record<string, unknown>).exclude_departments).toEqual([
      'Phòng Hành chính',
    ])
  })

  it('bỏ tick là câu cảnh báo biến mất', async () => {
    const user = userEvent.setup()
    build()

    await openExceptions(user)
    const chips = await screen.findAllByRole('button', { name: 'Phòng Hành chính' })
    await user.click(chips[1])
    expect(screen.getByText(CANH_BAO)).toBeInTheDocument()

    await user.click(chips[1])
    expect(screen.queryByText(CANH_BAO)).toBeNull()
  })

  it('im lặng khi loại trừ phòng KHÁC — trừ phòng người ta không phải lỗi', async () => {
    const user = userEvent.setup()
    build()

    await openExceptions(user)
    const chips = await screen.findAllByRole('button', { name: 'Phòng Kế toán' })
    await user.click(chips[1])

    expect(screen.queryByText(CANH_BAO)).toBeNull()
  })

  it('bắt cả phòng KIÊM NHIỆM, không riêng phòng chính', async () => {
    //  `profile.dept_ids` ở backend gom cả kiêm nhiệm (`departments_of`), nên trừ
    //  phòng kiêm nhiệm cũng làm mất phiếu y như trừ phòng chính.
    mockRoutes({ extraDepartmentIds: [10] }) // 10 = Phòng Kế toán
    const user = userEvent.setup()
    build()

    await openExceptions(user)
    const chips = await screen.findAllByRole('button', { name: 'Phòng Kế toán' })
    await user.click(chips[1])

    expect(await screen.findByText(/Phòng Kế toán là phòng của chính người này/)).toBeInTheDocument()
  })

  it('tài khoản CHƯA gắn hồ sơ thì không bao giờ cảnh báo — tên rỗng không khớp với gì', async () => {
    const user = userEvent.setup()
    build({ employeeId: 0 })

    await openExceptions(user)
    for (const name of ['Phòng Kế toán', 'Phòng Hành chính']) {
      await user.click((await screen.findAllByRole('button', { name }))[1])
    }

    expect(screen.queryByText(CANH_BAO)).toBeNull()
  })

  it('thiếu employee.read thì không cảnh báo được, và cũng KHÔNG gọi cửa phòng kiêm nhiệm', async () => {
    //  Cùng luật với A6: màn mượn dữ liệu nhân sự phải tự tắt khi thiếu quyền,
    //  kẻo người quản trị không có `employee.read` ăn toast 403 ngay lúc mở popup.
    permissions = { company: { read: true }, department: { read: true } }
    const user = userEvent.setup()
    build()

    await openExceptions(user)
    const chips = await screen.findAllByRole('button', { name: 'Phòng Hành chính' })
    await user.click(chips[1])

    expect(screen.queryByText(CANH_BAO)).toBeNull()
    const urls = apiGet.mock.calls.map((call) => call[0])
    expect(urls.some(isOwnerDepartmentsUrl)).toBe(false)
  })
})

describe('A10 — chưa mở vai trò nào', () => {
  it('roleId = null thì không gọi một API nào', async () => {
    build({ roleId: null })

    //  Hộp thoại luôn nằm trong cây React của trang Phân quyền, chỉ `open` là
    //  đổi — không gác thì đóng hộp vẫn nạp 2000 nhân sự cho mỗi lần render.
    await new Promise((resolve) => setTimeout(resolve, 20))
    expect(apiGet).not.toHaveBeenCalled()
  })

  it('bấm Lưu khi chưa có vai trò thì không PUT gì', async () => {
    const user = userEvent.setup()
    const { baseElement } = build({ roleId: null })

    //  Hộp đóng nên nút không có trong DOM — chính đó là điều cần khẳng định.
    expect(baseElement.querySelectorAll('[role="dialog"]')).toHaveLength(0)
    await user.click(document.body)
    expect(httpPut).not.toHaveBeenCalled()
  })
})
