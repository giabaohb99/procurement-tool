// bao-CR-530 — ô NSTM chính / dự phòng của màn Phân công phụ trách gõ tìm được (đại ca báo 30/09:
// «chỗ nhân viên trong phần phân công phụ trách không có search tên»). Trước đó là `Select`
// thường, danh sách nhân sự dài phải cuộn tay, trong khi ô Phòng / Phân loại ngay trên tìm được.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { CategoryAssigneeFormPage } from './category-assignee-form-page'

const EMPLOYEES = [
  { id: 1, full_name: 'Nguyễn Văn An', code: 'NV01', status: 'official', is_active: true },
  { id: 2, full_name: 'Trần Thị Bình', code: 'NV02', status: 'official', is_active: true },
  //  Đang thử việc: bao-CR-527 không mời vào ô chọn.
  { id: 3, full_name: 'Trần Văn Cường', code: 'NV03', status: 'probation', is_active: true },
]

vi.mock('@/core/api/http-client', () => ({
  httpClient: {
    get: async (url: string) => {
      if (url === '/api/employees') return { data: { items: EMPLOYEES } }
      return { data: { items: [] } }
    },
    post: vi.fn(),
  },
}))

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => true, canAccess: () => true }),
}))

vi.mock('@/modules/hr/hooks/use-departments', () => ({
  useDepartments: () => ({ data: { items: [] } }),
}))

function build() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/procurement/category-assignees/new']}>
        <CategoryAssigneeFormPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

/** Ô chọn gắn với nhãn — `SearchSelect` nhận `id` nên `getByLabelText` trỏ đúng ô. */
function field(label: RegExp) {
  return screen.getByLabelText(label)
}

/**
 * Danh sách thả xuống đang mở — khoanh trong khung popover chứa ô gõ tìm, vì nhãn của người đã
 * chọn cũng nằm trên chính ô chọn (tìm cả trang sẽ vớ nhầm).
 */
function openList() {
  const panel = screen.getByPlaceholderText('Gõ tên hoặc mã nhân viên…').closest('[data-slot="popover-content"]')
  if (!(panel instanceof HTMLElement)) throw new Error('danh sách chưa mở')
  return within(panel)
}

describe('CategoryAssigneeFormPage — ô NSTM gõ tìm được (bao-CR-530)', () => {
  it('finds a staff member by typing the name WITHOUT diacritics', async () => {
    const user = userEvent.setup()
    build()
    await screen.findByLabelText(/NSTM chính/)
    await user.click(field(/NSTM chính/))
    await user.type(screen.getByPlaceholderText('Gõ tên hoặc mã nhân viên…'), 'tran')

    const list = openList()
    expect(list.getByText('Trần Thị Bình · NV02')).toBeInTheDocument()
    expect(list.queryByText('Nguyễn Văn An · NV01')).not.toBeInTheDocument()
    //  bao-CR-527 giữ nguyên: người không «Chính thức» không có trong danh sách dù khớp chữ.
    expect(list.queryByText(/Trần Văn Cường/)).not.toBeInTheDocument()
  })

  it('finds by employee code too', async () => {
    const user = userEvent.setup()
    build()
    await screen.findByLabelText(/NSTM chính/)
    await user.click(field(/NSTM chính/))
    await user.type(screen.getByPlaceholderText('Gõ tên hoặc mã nhân viên…'), 'nv01')

    expect(openList().getByText('Nguyễn Văn An · NV01')).toBeInTheDocument()
  })

  it('backup list never offers the person already chosen as primary', async () => {
    const user = userEvent.setup()
    build()
    await screen.findByLabelText(/NSTM chính/)
    await user.click(field(/NSTM chính/))
    await user.click(openList().getByText('Nguyễn Văn An · NV01'))

    await user.click(field(/NSTM dự phòng/))
    const list = openList()
    expect(list.queryByText('Nguyễn Văn An · NV01')).not.toBeInTheDocument()
    expect(list.getByText('Trần Thị Bình · NV02')).toBeInTheDocument()
  })
})
