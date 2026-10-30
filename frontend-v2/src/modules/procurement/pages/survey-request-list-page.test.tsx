import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/core/auth/auth-store'
import type { ListParams } from '@/shared/types/api'
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

//  Chặn ở tầng HOOK dữ liệu để bắt được BỘ THAM SỐ màn này gửi đi — hai ô lọc
//  `item_group` / `assignee` chạy trên bảng DÒNG nên chỉ nhìn thấy ở đây.
const listCalls: ListParams[] = []

vi.mock('../hooks/use-purchase-documents', () => ({
  useSurveyRequests: (params: ListParams) => {
    listCalls.push(params)
    return {
      data: { total: rows.length, items: rows },
      isLoading: false,
      isError: false,
    }
  },
}))

//  Hai danh mục mượn của phân hệ khác: không chặn thì mỗi lần dựng màn là một
//  lượt gọi mạng thật trong jsdom.
vi.mock('../hooks/use-purchase-request-support', () => ({
  usePurchaseRequestItemGroups: () => ({
    data: { total: 1, items: [{ id: 5, name: 'Bao bì' }] },
  }),
}))
vi.mock('@/modules/hr/hooks/use-employees', () => ({
  useEmployees: () => ({
    data: { total: 2, items: [{ id: 9, code: 'NSU209', full_name: 'Trần Bảo' }, { id: 10, code: '', full_name: 'Người chưa có mã' }] },
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

function build(url = '/procurement/survey-requests') {
  //  `DataTable` gọi `useQueryClient` cho nút Tải lại — vẫn phải có provider dù
  //  mọi hook dữ liệu của màn này đã bị chặn.
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[url]}>
        <SurveyRequestListPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

function lastCall() {
  return listCalls[listCalls.length - 1]
}

beforeEach(() => {
  listCalls.length = 0
  localStorage.clear()
  sessionStorage.clear()
  useAuthStore.setState({ user: null })
})

describe('SurveyRequestListPage', () => {
  it('khổ rộng vẫn là BẢNG — thẻ chỉ thay ở khổ hẹp', () => {
    const { container } = build()

    expect(container.querySelector('table')).not.toBeNull()
    expect(screen.getByText('Mục đích')).toBeInTheDocument()
  })
})

describe('SurveyRequestListPage — hai ô lọc theo dòng hàng (bao-CR-443)', () => {
  it('sends the phân loại as a NAME, which is what the line column stores', () => {
    build('/procurement/survey-requests?item_group=Bao%20b%C3%AC')

    expect(lastCall().item_group).toBe('Bao bì')
  })

  it('sends the NSTM as an employee CODE — an id matches nothing and fails silently', () => {
    //  Backend so khớp CHÍNH XÁC với `SurveyRequestLine.assignee`, cột đó lưu mã
    //  nhân sự. Gửi số id thì danh sách rỗng mà không chỗ nào báo lỗi.
    build('/procurement/survey-requests?assignee=NSU209')

    expect(lastCall().assignee).toBe('NSU209')
  })

  it('sends neither param while both boxes sit at "Tất cả"', () => {
    build('/procurement/survey-requests?item_group=all&assignee=all')

    expect(lastCall().item_group).toBeUndefined()
    expect(lastCall().assignee).toBeUndefined()
  })

  it('puts both boxes on the toolbar', () => {
    build()

    expect(screen.getAllByLabelText('Lọc theo phân loại').length).toBeGreaterThan(0)
    expect(screen.getAllByLabelText('Lọc theo NSTM phụ trách').length).toBeGreaterThan(0)
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

/** kh-NT2-2 — chip lọc nhanh (doc `erp/nen-tang/14` §2.3). */
describe('SurveyRequestListPage — chip lọc nhanh', () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ['Date'] })
    vi.setSystemTime(new Date(2026, 9, 22, 9, 0))
    useAuthStore.setState({
      user: { id: 7, email: 'bao@dego.vn', full_name: 'Huỳnh Gia Bảo', employee_id: 9, emp_code: 'NSU209', permissions: {} },
    })
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  function chip(name: string) {
    return screen.getAllByRole('button', { name })[0]
  }

  it('Của tôi filters the lines I am the NSTM of, by employee CODE', () => {
    build()
    fireEvent.click(chip('Của tôi'))

    expect(lastCall().assignee).toBe('NSU209')
  })

  it('Chờ xử lý asks for requests thu mua still has to work on', () => {
    build()
    fireEvent.click(chip('Chờ xử lý'))

    expect(lastCall().status__in).toBe('approved,processing')
  })

  it('Chờ xử lý and a status picked in the box both apply — the box is not overwritten', () => {
    build('/procurement/survey-requests?status=processing')
    fireEvent.click(chip('Chờ xử lý'))

    expect(lastCall()).toMatchObject({ status: 'processing', status__in: 'approved,processing' })
  })

  it('Tháng này sets the ngày tạo range to the current month', () => {
    build()
    fireEvent.click(chip('Tháng này'))

    expect(lastCall()).toMatchObject({ request_date_from: '2026-10-01', request_date_to: '2026-10-31' })
  })
})

describe('SurveyRequestListPage — nút Xóa lọc', () => {
  it('clears the quick filters AND the advanced conditions in one go', async () => {
    //  Lỗi cũ: `filter.reset()` gọi sau cùng dựng lại URL từ bản lúc dựng, chép trả các
    //  ô lọc nhanh vừa xóa (`preserveParams`) — bấm Xóa lọc mà bảng vẫn lọc nguyên.
    build(
      '/procurement/survey-requests?company_id=1&status=approved&assignee=NSU209&pending=1&code__contains=YCBG',
    )
    //  Hai nút cùng tên "Bộ lọc": popover nâng cao (khổ rộng) và tờ trượt (khổ hẹp) — nút
    //  *Xóa lọc* nằm ở tờ trượt.
    const sheetTrigger = screen
      .getAllByRole('button', { name: 'Bộ lọc' })
      .find((button) => button.getAttribute('data-slot') === 'sheet-trigger')
    if (!sheetTrigger) throw new Error('Không thấy nút mở tờ lọc')
    fireEvent.click(sheetTrigger)
    fireEvent.click(await screen.findByRole('button', { name: 'Xóa lọc' }))

    const call = lastCall()
    expect(call.company_id).toBeUndefined()
    expect(call.status).toBeUndefined()
    expect(call.assignee).toBeUndefined()
    expect(call.status__in).toBeUndefined()
    expect(call.code__contains).toBeUndefined()
  })
})
