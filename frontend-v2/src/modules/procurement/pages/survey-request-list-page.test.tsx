import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { SurveyRequestListPage } from './survey-request-list-page'
import type { SurveyRequest } from '../types/purchase-document'

const rows: SurveyRequest[] = [
  {
    id: 1,
    code: 'YCBGDEMO01',
    company_id: 1,
    requester: 'Nhân viên (Demo)',
    department: 'Phòng Kinh doanh',
    purpose: 'Khảo sát giá bao bì cho dây chuyền chiết rót số 2',
    request_date: '2026-03-02',
    status: 'survey_done',
    note: '',
    created_at: '2026-03-02T09:15:00',
  },
]

vi.mock('../hooks/use-purchase-documents', () => ({
  useSurveyRequests: () => ({
    data: { total: rows.length, items: rows },
    isLoading: false,
    isError: false,
  }),
}))

// Hai danh mục chỉ để đổ ô chọn — màn này không nói gì về chúng.
vi.mock('@/modules/hr/hooks/use-companies', () => ({
  useCompanies: () => ({ data: { items: [] } }),
}))
vi.mock('@/modules/hr/hooks/use-departments', () => ({
  useDepartments: () => ({ data: { items: [] } }),
}))

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => true, canAccess: () => true }),
}))

function build() {
  //  `DataTable` gọi `useQueryClient` cho nút Tải lại — vẫn phải có provider dù
  //  mọi hook dữ liệu của màn này đã bị chặn.
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/procurement/survey-requests']}>
        <SurveyRequestListPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => localStorage.clear())

describe('SurveyRequestListPage', () => {
  it('khổ rộng vẫn là BẢNG — thẻ chỉ thay ở khổ hẹp', () => {
    const { container } = build()

    expect(container.querySelector('table')).not.toBeNull()
    expect(screen.getByText('Mục đích')).toBeInTheDocument()
  })
})

/**
 * Khổ điện thoại — bảng đổi sang THẺ, xem `SurveyRequestCard`.
 *
 * Bảng khai 8 cột, bề rộng tự nhiên ~1330px trong khung ~322px: phần nhìn thấy
 * được là *Mã phiếu* cộng một mẩu *Mục đích*, còn trạng thái — thứ quyết định
 * phiếu này còn việc gì để làm hay không — thì nằm ngoài mép phải.
 *
 * `setup.ts` cố định `matchMedia` ở khổ desktop cho cả bộ test, nên khổ hẹp phải
 * nói rõ ra ngay tại đây.
 */
describe('SurveyRequestListPage — khổ điện thoại', () => {
  beforeEach(() => {
    vi.stubGlobal('matchMedia', (query: string) => ({
      matches: true,
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }))
  })
  afterEach(() => vi.unstubAllGlobals())

  it('bày MỤC ĐÍCH và TRẠNG THÁI — hai thứ nằm ngoài mép phải của bảng', () => {
    const { container } = build()

    expect(container.querySelector('table')).toBeNull()
    expect(
      screen.getByText('Khảo sát giá bao bì cho dây chuyền chiết rót số 2'),
    ).toBeInTheDocument()
    expect(screen.getByText('Đã khảo sát')).toBeInTheDocument()
  })

  it('mã phiếu vẫn có mặt, nhưng ở dòng PHỤ — mười phiếu mở đầu giống hệt nhau', () => {
    build()

    expect(screen.getByText('YCBGDEMO01')).toBeInTheDocument()
    // Mục đích mới là tiêu đề: nó là thứ phân biệt các phiếu với nhau.
    const card = screen.getByRole('button', { name: /Khảo sát giá bao bì/ })
    expect(card).toBeInTheDocument()
  })

  it('câu gợi ý tìm kiếm rút gọn còn HAI vế — ô tìm chỉ rộng ~134px', () => {
    //  Ba vế (~137px) vẫn bị xén giữa chừng, tức bản "rút gọn" không giải quyết
    //  được gì so với bản đầy đủ. Đo ngày 14/09/2026 trên máy 390px.
    build()

    expect(screen.getByPlaceholderText('Tìm phiếu, SP…')).toBeInTheDocument()
  })
})
