import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/core/auth/auth-store'
import type { ListParams } from '@/shared/types/api'
import { PurchaseRequestListPage } from './purchase-request-list-page'

//  Chặn ở tầng HOOK dữ liệu chứ không ở `@/core/api`: màn này phải bắt được BỘ
//  THAM SỐ nó gửi đi, mà hai ô lọc của bao-CR-443 (`item_group`, `assignee`)
//  chạy trên bảng DÒNG nên chỉ nhìn thấy ở đây.
const listCalls: ListParams[] = []

vi.mock('../hooks/use-purchase-documents', () => ({
  usePurchaseRequests: (params: ListParams) => {
    listCalls.push(params)
    return { data: { total: 0, items: [] }, isLoading: false, isError: false }
  },
}))

//  Bốn danh mục mượn của phân hệ khác: không chặn thì mỗi lần dựng màn là một
//  lượt gọi mạng thật trong jsdom.
vi.mock('../hooks/use-purchase-request-support', () => ({
  usePurchaseRequestItemGroups: () => ({ data: { total: 1, items: [{ id: 5, name: 'Bao bì' }] } }),
}))
vi.mock('@/modules/hr/hooks/use-companies', () => ({
  useCompanies: () => ({ data: { total: 0, items: [] } }),
}))
vi.mock('@/modules/hr/hooks/use-departments', () => ({
  useDepartments: () => ({ data: { total: 0, items: [] } }),
}))
vi.mock('@/modules/hr/hooks/use-employees', () => ({
  useEmployees: () => ({
    data: { total: 1, items: [{ id: 9, code: 'NSU209', full_name: 'Trần Bảo' }] },
  }),
}))

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => true, canAccess: () => true }),
}))

function build(url = '/procurement/purchase-requests') {
  //  `DataTable` gọi `useQueryClient` cho nút Tải lại — vẫn phải có provider dù
  //  mọi hook dữ liệu của màn này đã bị chặn.
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[url]}>
        <PurchaseRequestListPage />
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

describe('PurchaseRequestListPage — hai ô lọc của bao-CR-443', () => {
  it('sends the phân loại as a NAME, which is what the line column stores', () => {
    build('/procurement/purchase-requests?item_group=Bao%20b%C3%AC')

    expect(lastCall().item_group).toBe('Bao bì')
  })

  it('sends the NSTM as an employee CODE — an id matches nothing and fails silently', () => {
    //  Backend so khớp CHÍNH XÁC với `PurchaseRequestItem.assignee`, cột đó lưu
    //  mã nhân sự. Gửi số id thì danh sách rỗng mà không chỗ nào báo lỗi.
    build('/procurement/purchase-requests?assignee=NSU209')

    expect(lastCall().assignee).toBe('NSU209')
  })

  it('sends neither param while both boxes sit at "Tất cả"', () => {
    build('/procurement/purchase-requests?item_group=all&assignee=all')

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
 * kh-NT2-2 — chip lọc nhanh (doc `erp/nen-tang/14` §2.1).
 *
 * Chip chỉ là lối tắt GHI VÀO tham số lọc đã có (`assignee`, `request_date_*`,
 * `need_date_*`), nên ô chọn / ô ngày tương ứng cũng hiện đúng giá trị đó.
 */
describe('PurchaseRequestListPage — chip lọc nhanh', () => {
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
    expect(chip('Của tôi')).toHaveAttribute('aria-pressed', 'true')
  })

  it('Của tôi is off again on a second click', () => {
    build('/procurement/purchase-requests?assignee=NSU209')
    fireEvent.click(chip('Của tôi'))

    expect(lastCall().assignee).toBeUndefined()
  })

  it('Của tôi is not pressed while the NSTM box points at someone else', () => {
    build('/procurement/purchase-requests?assignee=NSU100')

    expect(chip('Của tôi')).toHaveAttribute('aria-pressed', 'false')
  })

  it('Của tôi is disabled and says why for an account with no employee record', () => {
    useAuthStore.setState({ user: { id: 8, email: 'kho@dego.vn', full_name: 'kho@dego.vn', emp_code: '', permissions: {} } })
    build()

    expect(chip('Của tôi')).toBeDisabled()
    expect(chip('Của tôi')).toHaveAttribute('title', expect.stringContaining('chưa gắn hồ sơ nhân sự'))
  })

  it('Tháng này sets the ngày lập phiếu range to the current month', () => {
    build()
    fireEvent.click(chip('Tháng này'))

    expect(lastCall()).toMatchObject({
      request_date_from: '2026-10-01',
      request_date_to: '2026-10-31',
    })
  })

  it('Sắp tới hạn sets the ngày cần hàng range to the next seven days, today included', () => {
    build()
    fireEvent.click(chip('Sắp tới hạn'))

    expect(lastCall()).toMatchObject({ need_date_from: '2026-10-22', need_date_to: '2026-10-28' })
  })

  it('chips stack with each other and with the urgent chip', () => {
    //  Ba lần bấm liền tay: mỗi chip ghi URL bằng hàm cập nhật nên không lần nào đè lần trước.
    build()
    fireEvent.click(chip('Gấp'))
    fireEvent.click(chip('Tháng này'))
    fireEvent.click(chip('Của tôi'))

    expect(lastCall()).toMatchObject({
      is_urgent: true,
      assignee: 'NSU209',
      request_date_from: '2026-10-01',
      request_date_to: '2026-10-31',
    })
  })

  it('a range that matches this month on one end only does not light the chip', () => {
    build('/procurement/purchase-requests?request_date_from=2026-10-01')

    expect(chip('Tháng này')).toHaveAttribute('aria-pressed', 'false')
  })
})

describe('PurchaseRequestListPage — nút Xóa lọc', () => {
  it('clears EVERY quick filter, not just the last one', async () => {
    //  Lỗi cũ (phát hiện ở kh-NT2-2): mười setter gọi liền nhau, react-router đưa cho
    //  mỗi lần URL lúc dựng nên chỉ ô cuối bị xóa — bảng vẫn lọc theo công ty, trạng
    //  thái, gấp... mà người dùng tưởng đã xóa hết, và bản nhớ giữ nguyên cho lần sau.
    build(
      '/procurement/purchase-requests?company_id=1&status=approved&is_urgent=true&assignee=NSU209&request_date_from=2026-10-01&request_date_to=2026-10-31&q=bao',
    )
    //  Hai nút cùng tên «Bộ lọc»: popover nâng cao (khổ rộng) và tờ trượt (khổ hẹp) — nút
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
    expect(call.is_urgent).toBeUndefined()
    expect(call.assignee).toBeUndefined()
    expect(call.request_date_from).toBeUndefined()
    expect(call.request_date_to).toBeUndefined()
    //  Ô tìm kiếm không phải bộ lọc — giữ nguyên.
    expect(call.code).toBe('bao')
  })
})

describe('PurchaseRequestListPage — câu bảng rỗng', () => {
  it('says the table is empty BECAUSE of the filters when a filter came back from memory', () => {
    build('/procurement/purchase-requests?is_urgent=true')

    expect(screen.getAllByText(/khớp bộ lọc đang chọn/).length).toBeGreaterThan(0)
  })

  it('keeps the plain empty sentence when nothing is filtered', () => {
    build()

    expect(screen.queryByText(/khớp bộ lọc đang chọn/)).toBeNull()
  })
})
