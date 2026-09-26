import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { EmployeeDepartmentCard } from './employee-department-card'

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

const DEPARTMENTS = {
  items: [
    { id: 1, name: 'Phòng Hành chính', company_id: 1 },
    { id: 2, name: 'Phòng Kế toán', company_id: 1 },
    { id: 3, name: 'Phòng Công nghệ thông tin', company_id: 1 },
  ],
  total: 3,
}

function newQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
}

//  Truyền sẵn một `queryClient` khi cần dựng lại thẻ trên cùng bộ đệm — đó là
//  cảnh «quay ra danh sách rồi mở lại hồ sơ», khác hẳn cảnh mở lần đầu.
function build(queryClient = newQueryClient()) {
  const { unmount } = render(
    <QueryClientProvider client={queryClient}>
      <EmployeeDepartmentCard
        employeeId={9}
        companyId={1}
        primaryDepartmentId={1}
        canWrite
        isSelf={false}
      />
    </QueryClientProvider>,
  )

  return { queryClient, unmount }
}

beforeEach(() => {
  apiGet.mockReset()
  httpPut.mockReset()
  httpPut.mockResolvedValue({ data: { success: true, message: 'Đã cập nhật', data: null } })
  apiGet.mockImplementation((url: string) =>
    url === '/api/employees/9/departments'
      ? Promise.resolve({ primary_department_id: 1, extra_department_ids: [2, 3] })
      : Promise.resolve(DEPARTMENTS),
  )
})

describe('EmployeeDepartmentCard', () => {
  it('mở lại hồ sơ khi bộ đệm còn nóng thì vẫn giữ nguyên phòng kiêm nhiệm', async () => {
    //  Cùng họ lỗi với bao-CR-491 (đại ca báo 25/09/2026), rà ra ở bao-CR-492.
    //  Lần mở thứ hai React Query trả dữ liệu từ bộ đệm NGAY ở lượt render đầu,
    //  mà ở lượt đầu `useHasChanged` luôn trả `false` — bản cũ khởi tạo state
    //  bằng `[]` nên thẻ hiện ra KHÔNG TICK phòng nào.
    //
    //  Khẳng định ở đây là HẬU QUẢ thật chứ không phải vẻ ngoài: cửa lưu nhận
    //  cả danh sách chứ không nhận phần chênh, nên người dùng bấm «Lưu kiêm
    //  nhiệm» trên một thẻ trống là XÓA SẠCH phòng kiêm nhiệm có thật.
    const nguoi = userEvent.setup()

    const lanDau = build()
    expect(await screen.findByRole('button', { name: /Lưu kiêm nhiệm/ })).toBeEnabled()

    lanDau.unmount()
    build(lanDau.queryClient)

    await nguoi.click(await screen.findByRole('button', { name: /Lưu kiêm nhiệm/ }))
    expect(httpPut).toHaveBeenCalledWith('/api/employees/9/departments', {
      extra_department_ids: [2, 3],
    })
  })

  it('chưa ai có kiêm nhiệm thì lưu đúng danh sách rỗng, không bịa ra phòng nào', async () => {
    //  Mặt kia của chốt trên: khởi tạo đọc thẳng dữ liệu máy chủ nên phải phân
    //  biệt được «máy chủ trả rỗng» với «chưa tải xong».
    apiGet.mockImplementation((url: string) =>
      url === '/api/employees/9/departments'
        ? Promise.resolve({ primary_department_id: 1, extra_department_ids: [] })
        : Promise.resolve(DEPARTMENTS),
    )
    const nguoi = userEvent.setup()

    const lanDau = build()
    expect(await screen.findByRole('button', { name: /Lưu kiêm nhiệm/ })).toBeEnabled()
    lanDau.unmount()
    build(lanDau.queryClient)

    await nguoi.click(await screen.findByRole('button', { name: /Lưu kiêm nhiệm/ }))
    expect(httpPut).toHaveBeenCalledWith('/api/employees/9/departments', {
      extra_department_ids: [],
    })
  })
})
