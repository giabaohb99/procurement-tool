import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
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

interface RouteData {
  companies?: unknown[]
  departments?: unknown[]
  employees?: unknown[]
  /** Phạm vi đã lưu, tra theo `roleId`. */
  scopes?: Record<number, Record<string, unknown>>
}

function mockRoutes(data: RouteData = {}) {
  apiGet.mockImplementation((url: string) => {
    if (url.includes('/scope')) {
      const roleId = Number(url.match(/roles\/(\d+)\/scope/)?.[1] ?? 0)
      return Promise.resolve(data.scopes?.[roleId] ?? {})
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
    return Promise.reject(new Error(`URL không được khai trong test: ${url}`))
  })
}

function build(props: Partial<Parameters<typeof UserScopeDialog>[0]> = {}) {
  const onClose = vi.fn()
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  const view = render(
    <QueryClientProvider client={client}>
      <UserScopeDialog userId={31} roleId={7} roleName="Kế toán" onClose={onClose} {...props} />
    </QueryClientProvider>,
  )
  return { ...view, onClose, client }
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

    await screen.findByRole('button', { name: 'DEGO' })
    await user.click(screen.getByRole('button', { name: 'DEGO' }))
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
    build()
    await screen.findByRole('button', { name: 'DEGO' })
    //  "Để trống = không thấy gì" là cách hiểu tự nhiên và ngược hẳn sự thật.
    expect(
      screen.getByText(/Để trống một mục = không giới hạn chiều đó/),
    ).toBeInTheDocument()
  })

  it('không tick gì mà Lưu thì gửi mảng rỗng, không gửi cả danh mục', async () => {
    const user = userEvent.setup()
    build()
    await screen.findByRole('button', { name: 'DEGO' })
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
    const { rerender, client } = build({ roleId: 7 })

    await waitFor(() =>
      expect(screen.getByRole('button', { name: 'DEGO' })).toHaveAttribute('aria-pressed', 'true'),
    )

    rerender(
      <QueryClientProvider client={client}>
        <UserScopeDialog userId={31} roleId={8} roleName="Thu mua" onClose={vi.fn()} />
      </QueryClientProvider>,
    )

    await waitFor(() =>
      expect(screen.getByRole('button', { name: 'DGF' })).toHaveAttribute('aria-pressed', 'true'),
    )
    //  Chip của vai trò cũ phải TẮT. Giữ lại là lưu nhầm phạm vi vai trò này
    //  sang vai trò kia mà không ai thấy gì bất thường.
    expect(screen.getByRole('button', { name: 'DEGO' })).toHaveAttribute('aria-pressed', 'false')
  })
})

describe('A5 — cùng một phòng vừa được xem vừa bị loại trừ', () => {
  it('màn hình CHO tick cả hai, và đó là mâu thuẫn im lặng', async () => {
    //  Backend xử "loại trừ thắng" (`apply_scope`), nên tick cả hai = chọn xong
    //  tự loại mình ra. Hộp thoại hiện không cảnh báo gì; bài kiểm ghi lại đúng
    //  hành vi hôm nay để lần sau thêm cảnh báo thì phải sửa ở đây.
    const user = userEvent.setup()
    build()

    const chipsKeToan = await screen.findAllByRole('button', { name: 'Phòng Kế toán' })
    expect(chipsKeToan).toHaveLength(2) // 1 ở "được xem", 1 ở "loại trừ"
    await user.click(chipsKeToan[0])
    await user.click(chipsKeToan[1])
    await user.click(screen.getByRole('button', { name: 'Lưu phạm vi' }))

    await waitFor(() => expect(httpPut).toHaveBeenCalled())
    const body = httpPut.mock.calls[0][1] as Record<string, unknown>
    expect(body.departments).toEqual(['Phòng Kế toán'])
    expect(body.exclude_departments).toEqual(['Phòng Kế toán'])
    //  Không có câu nào nói cho người khai biết loại trừ sẽ thắng.
    expect(screen.queryByText(/loại trừ.*thắng/i)).toBeNull()
  })
})

describe('A6 — ba danh mục có cổng quyền (09-D)', () => {
  it('thiếu employee.read thì KHÔNG gọi /api/employees', async () => {
    permissions = { company: { read: true }, department: { read: true } }
    build()

    await screen.findByRole('button', { name: 'DEGO' })
    const urls = apiGet.mock.calls.map((c) => c[0])
    expect(urls).not.toContain('/api/employees')
    expect(urls).toContain('/api/companies')
  })

  it('thiếu quyền thì nói ra, không để một ô rỗng', async () => {
    //  403 trên GET KHÔNG bật toast (`core/api/http-client.ts`), nên ô rỗng là
    //  tất cả những gì người khai quyền nhìn thấy — và họ đọc ra thành "công ty
    //  này chưa khai phòng ban nào" rồi khai phạm vi hụt.
    permissions = { company: { read: true } }
    build()

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
    mockRoutes({ companies: [], departments: [] })
    build()

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

    await screen.findByRole('button', { name: 'DEGO' })
    await user.click(screen.getByRole('button', { name: 'DEGO' }))
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

    await screen.findByRole('button', { name: 'DEGO' })
    await user.click(screen.getByRole('button', { name: 'Lưu phạm vi' }))

    await waitFor(() => expect(onClose).toHaveBeenCalledTimes(1))
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
