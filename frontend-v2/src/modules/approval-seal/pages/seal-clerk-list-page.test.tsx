import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { TooltipProvider } from '@/shared/ui/tooltip'
import { SealClerkListPage } from './seal-clerk-list-page'
import type { SealClerkGroup } from '../types/seal-clerk'

const MOCK_CLERKS: SealClerkGroup[] = [
  {
    employee_id: 25,
    anchor_id: 1,
    employee_name: 'Thái Thị Thu Hiền',
    employee_code: 'NSU003',
    company_count: 3,
    companies: [
      { id: 1, name: 'CÔNG TY TNHH DEGO HOLDING', logo: '' },
      { id: 2, name: 'CÔNG TY TNHH XUẤT NHẬP KHẨU IDA GLOBAL', logo: '' },
    ],
    is_head: true,
    status: 1,
    status_label: 'Đang hoạt động',
  },
  {
    employee_id: 28,
    anchor_id: 2,
    employee_name: 'Võ Thanh Huyền',
    employee_code: 'NSU006',
    company_count: 1,
    companies: [
      { id: 1, name: 'CÔNG TY TNHH DEGO HOLDING', logo: '' },
    ],
    is_head: false,
    status: 1,
    status_label: 'Đang hoạt động',
  },
]

vi.mock('../hooks/use-seal-clerks', () => ({
  useSealClerks: () => ({
    data: { total: MOCK_CLERKS.length, items: MOCK_CLERKS },
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
    isFetching: false,
  }),
  useSyncSealClerks: () => ({
    mutate: vi.fn(),
    isPending: false,
  }),
}))

vi.mock('@/modules/hr/hooks/use-companies', () => ({
  useCompanies: () => ({
    data: {
      total: 2,
      items: [
        { id: 1, name: 'CÔNG TY TNHH DEGO HOLDING' },
        { id: 2, name: 'CÔNG TY TNHH XUẤT NHẬP KHẨU IDA GLOBAL' },
      ],
    },
  }),
}))

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: () => true,
    canAccess: () => true,
  }),
}))

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <TooltipProvider>
          <SealClerkListPage />
        </TooltipProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('SealClerkListPage', () => {
  it('hiển thị tiêu đề, thẻ KPI và danh sách văn thư', () => {
    renderPage()

    expect(screen.getByText('Phân công văn thư đóng dấu')).toBeInTheDocument()
    expect(screen.getByText('Tổng số văn thư')).toBeInTheDocument()
    expect(screen.getByText('Thái Thị Thu Hiền')).toBeInTheDocument()
    expect(screen.getByText('Võ Thanh Huyền')).toBeInTheDocument()
    expect(screen.getByText('Mã: NSU003')).toBeInTheDocument()
    expect(screen.getByText('Văn thư tổng')).toBeInTheDocument()
  })

  //  Bài kiểm này nhắc lại một LỖI ĐÃ XẢY RA (22/09/2026), đừng xóa: bản cũ
  //  phân trang phía máy chủ nhưng đếm và lọc trên `data.items` = trang đang
  //  xem, mà API không biết lọc theo `is_head`. Quá một trang là bấm thẻ "Đa
  //  pháp nhân 2" ra bảng rỗng vì hai người đó nằm ở trang sau.
  it('lọc bảng theo thẻ đếm đang chọn, đếm trên toàn bộ danh sách', async () => {
    const user = userEvent.setup()
    renderPage()

    const card = screen.getByRole('button', { name: /Đa pháp nhân/ })
    expect(within(card).getByText('1')).toBeInTheDocument()
    expect(card).toHaveAttribute('aria-pressed', 'false')

    await user.click(card)

    expect(card).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByText('Thái Thị Thu Hiền')).toBeInTheDocument()
    expect(screen.queryByText('Võ Thanh Huyền')).not.toBeInTheDocument()

    // Bấm lại đúng thẻ đang chọn = bỏ lọc, cả hai người hiện lại.
    await user.click(card)
    expect(screen.getByText('Võ Thanh Huyền')).toBeInTheDocument()
  })

  it('phân biệt bảng rỗng vì bộ lọc với bảng rỗng vì chưa có dữ liệu', async () => {
    const user = userEvent.setup()
    renderPage()

    // Không ai đang nghỉ phép trong dữ liệu mẫu → lọc ra rỗng.
    await user.click(screen.getByRole('button', { name: /Nghỉ phép/ }))

    expect(screen.getByText('Không có văn thư nào khớp bộ lọc đang chọn.')).toBeInTheDocument()
  })
})
