import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
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
})
