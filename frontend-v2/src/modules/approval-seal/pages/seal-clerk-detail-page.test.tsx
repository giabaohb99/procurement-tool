import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { TooltipProvider } from '@/shared/ui/tooltip'
import { SealClerkDetailPage } from './seal-clerk-detail-page'

const { mockClerk, mockAssign, mockEmployee, mockCompanies, mockSyncMutate } = vi.hoisted(() => ({
  mockClerk: {
    id: 12,
    employee_id: 25,
    company_id: 1,
    is_head: true,
    status: 1,
    employee_name: 'Thái Thị Thu Hiền',
    employee_code: 'NSU003',
    company_name: 'CÔNG TY TNHH DEGO HOLDING',
    status_label: 'Đang hoạt động',
  },
  mockAssign: {
    employee_id: 25,
    company_ids: [1, 2],
    is_head: true,
    status: 1,
  },
  mockEmployee: {
    id: 25,
    code: 'NSU003',
    full_name: 'Thái Thị Thu Hiền',
    email: 'hien.ttt@degoholding.com',
    phone: '0901234567',
    department_name: 'Phòng Hành chính Nhân sự',
    position: 'Chuyên viên Hành chính',
    company_name: 'CÔNG TY TNHH DEGO HOLDING',
    status_label: 'Chính thức',
    avatar: '',
  },
  mockCompanies: [
    { id: 1, name: 'CÔNG TY TNHH DEGO HOLDING', tax_code: '0312345678', logo: '' },
    { id: 2, name: 'CÔNG TY TNHH XUẤT NHẬP KHẨU IDA GLOBAL', tax_code: '0318765432', logo: '' },
  ],
  mockSyncMutate: vi.fn(),
}))

vi.mock('../hooks/use-seal-clerks', () => ({
  useSealClerk: () => ({
    data: mockClerk,
    isLoading: false,
    isError: false,
  }),
  useSealClerkByEmployee: () => ({
    data: mockAssign,
    isLoading: false,
    isError: false,
  }),
  useSyncSealClerks: () => ({
    mutate: mockSyncMutate,
    isPending: false,
  }),
}))

vi.mock('@/modules/hr/hooks/use-employees', () => ({
  useEmployee: () => ({
    data: mockEmployee,
    isLoading: false,
    isError: false,
  }),
}))

vi.mock('@/modules/hr/api/company-api', () => ({
  companyApi: {
    list: vi.fn().mockResolvedValue({
      total: mockCompanies.length,
      items: mockCompanies,
    }),
  },
}))

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: () => true,
    canAccess: () => true,
  }),
}))

vi.mock('@/modules/procurement/components/document-comments', () => ({
  DocumentComments: () => <div data-testid="document-comments">Document Comments</div>,
}))

vi.mock('@/shared/audit/audit-timeline', () => ({
  AuditTimeline: () => <div data-testid="audit-timeline">Audit Timeline</div>,
}))

function renderDetailPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/approval-seal/clerks/12']}>
        <TooltipProvider>
          <Routes>
            <Route path="/approval-seal/clerks/:id" element={<SealClerkDetailPage />} />
          </Routes>
        </TooltipProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('SealClerkDetailPage', () => {
  it('hiển thị đủ tiêu đề, cấu hình phân công, thông tin nhân sự và hai khối dấu vết', async () => {
    renderDetailPage()

    // Header & metadata
    expect(screen.getAllByText('Thái Thị Thu Hiền').length).toBeGreaterThan(0)
    expect(screen.getAllByText('NSU003').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Phòng Hành chính Nhân sự').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Chuyên viên Hành chính').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Văn thư tổng').length).toBeGreaterThan(0)

    // Cột trái: Cấu hình phân công đóng dấu — phần việc chính của trang
    expect(screen.getByText('Cấu hình phân công đóng dấu')).toBeInTheDocument()
    expect(screen.getByText('Trạng thái phân công')).toBeInTheDocument()
    expect(screen.getAllByText(/Văn thư tổng/i).length).toBeGreaterThan(0)

    // Cột phải: Thông tin nhân sự (chỉ đọc)
    expect(screen.getByText('Thông tin nhân sự')).toBeInTheDocument()
    expect(screen.getByText('hien.ttt@degoholding.com')).toBeInTheDocument()
    expect(screen.getByText('0901234567')).toBeInTheDocument()

    expect(screen.getByTestId('document-comments')).toBeInTheDocument()
    expect(screen.getByTestId('audit-timeline')).toBeInTheDocument()
  })

  //  Thẻ «Tổng quan phân công» bỏ ngày 22/09/2026 — nó chỉ soi lại ba ô đang
  //  chỉnh ở cột trái (và soi cả thay đổi CHƯA LƯU), nên không nói được điều gì
  //  mà nhìn sang cột trái không thấy. Bài kiểm này giữ cho nó đừng mọc lại.
  it('không dựng lại thẻ tổng quan soi ngược cấu hình bên trái', () => {
    renderDetailPage()

    expect(screen.queryByText('Tổng quan phân công')).not.toBeInTheDocument()
    expect(screen.queryByText('Sẵn sàng nhận phiếu')).not.toBeInTheDocument()
  })

  it('cho phép gỡ nhanh công ty khỏi danh sách phụ trách', async () => {
    renderDetailPage()

    // Chờ danh sách công ty tải xong
    const removeButtons = await screen.findAllByTitle(/Gỡ/i)
    expect(removeButtons.length).toBeGreaterThan(0)

    // Click nút gỡ
    fireEvent.click(removeButtons[0])

    // Kiểm tra nút Lưu thay đổi được kích hoạt (dirty state)
    expect(screen.getByText('Lưu thay đổi')).toBeInTheDocument()
  })
})
