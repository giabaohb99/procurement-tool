import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/core/auth/auth-store'
import type { ListParams } from '@/shared/types/api'
import { PurchaseOrderListPage } from './purchase-order-list-page'

//  Chặn ở tầng HOOK dữ liệu chứ không ở `@/core/api`: màn này phải bắt được BỘ
//  THAM SỐ nó gửi đi, mà hai ô lọc của bao-CR-443 (`item_group`, `invoice_no`)
//  chạy trên bảng DÒNG và bảng LẦN GIAO nên chỉ nhìn thấy ở đây.
const listCalls: ListParams[] = []
//  Dòng trả về cho bảng — rỗng mặc định; bài bao-CR-705 nạp dòng để soi cột Phòng xử lý.
const listItems: Record<string, unknown>[] = []

vi.mock('../hooks/use-purchase-documents', () => ({
  usePurchaseOrders: (params: ListParams) => {
    listCalls.push(params)
    return { data: { total: listItems.length, items: listItems }, isLoading: false, isError: false }
  },
}))

//  Ba danh mục mượn của phân hệ khác: không chặn thì mỗi lần dựng màn là một
//  lượt gọi mạng thật trong jsdom.
vi.mock('../hooks/use-purchase-request-support', () => ({
  usePurchaseRequestItemGroups: () => ({ data: { total: 1, items: [{ id: 5, name: 'Bao bì' }] } }),
}))
vi.mock('@/modules/hr/hooks/use-companies', () => ({
  useCompanies: () => ({ data: { total: 0, items: [] } }),
}))
vi.mock('@/modules/hr/hooks/use-employees', () => ({
  useEmployees: () => ({ data: { total: 0, items: [] } }),
}))
vi.mock('@/modules/production/hooks/use-suppliers', () => ({
  useSuppliers: () => ({ data: { total: 0, items: [] } }),
}))

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => true, canAccess: () => true }),
}))

function build(url = '/procurement/purchase-orders') {
  //  `DataTable` gọi `useQueryClient` cho nút Tải lại — vẫn phải có provider dù
  //  mọi hook dữ liệu của màn này đã bị chặn.
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[url]}>
        <PurchaseOrderListPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

function lastCall() {
  return listCalls[listCalls.length - 1]
}

beforeEach(() => {
  listCalls.length = 0
  listItems.length = 0
  localStorage.clear()
  sessionStorage.clear()
  useAuthStore.setState({ user: null })
})

describe('PurchaseOrderListPage — hai ô lọc của bao-CR-443', () => {
  it('sends the phân loại as a NAME — the line column copies the text, not the id', () => {
    build('/procurement/purchase-orders?item_group=Bao%20b%C3%AC')

    expect(lastCall().item_group).toBe('Bao bì')
  })

  it('sends the invoice number as typed — the backend matches it with CONTAINS', () => {
    //  Số hóa đơn được hỏi ở CẢ dòng hàng lẫn lần giao, và khớp kiểu CHỨA, nên
    //  gõ một mẩu vẫn ra kết quả. Đó là lý do ô này là ô CHỮ chứ không phải ô chọn.
    build('/procurement/purchase-orders?invoice_no=0001234')

    expect(lastCall().invoice_no).toBe('0001234')
  })

  it('sends neither param when the phân loại sits at "Tất cả" and the ô hóa đơn is empty', () => {
    build('/procurement/purchase-orders?item_group=all&invoice_no=')

    expect(lastCall().item_group).toBeUndefined()
    expect(lastCall().invoice_no).toBeUndefined()
  })

  it('keeps the older filters working alongside the two new ones', () => {
    build('/procurement/purchase-orders?status=approved&item_group=Bao%20b%C3%AC&invoice_no=77')

    expect(lastCall()).toMatchObject({
      status: 'approved',
      item_group: 'Bao bì',
      invoice_no: '77',
    })
  })

  it('puts both boxes on the toolbar', () => {
    build()

    expect(screen.getAllByLabelText('Lọc theo phân loại').length).toBeGreaterThan(0)
    expect(screen.getAllByLabelText('Lọc theo số hóa đơn').length).toBeGreaterThan(0)
  })
})

/** kh-NT2-2 — chip lọc nhanh (doc `erp/nen-tang/14` §2.2). */
describe('PurchaseOrderListPage — chip lọc nhanh', () => {
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

  it('Của tôi filters by NSPT as the employee ID — `nspt_id` is a number, not the NSU code', () => {
    build()
    fireEvent.click(chip('Của tôi'))

    expect(lastCall().nspt_id).toBe(9)
  })

  it('Thiếu chứng từ asks for orders with no documents or only part of them', () => {
    build()
    fireEvent.click(chip('Thiếu chứng từ'))

    expect(lastCall().document_status__in).toBe('none,partial')
  })

  it('Thiếu chứng từ is off again on a second click', () => {
    build('/procurement/purchase-orders?missing_docs=1')
    fireEvent.click(chip('Thiếu chứng từ'))

    expect(lastCall().document_status__in).toBeUndefined()
  })

  it('Thiếu chứng từ steps aside while the advanced filter joins its conditions with OR', () => {
    build('/procurement/purchase-orders?missing_docs=1&code__contains=A&pr_code__contains=B&conjunction=or')

    expect(lastCall().document_status__in).toBeUndefined()
    expect(chip('Thiếu chứng từ')).toBeDisabled()
  })

  it('Tháng này sets the ngày đặt range to the current month', () => {
    build()
    fireEvent.click(chip('Tháng này'))

    expect(lastCall()).toMatchObject({ order_date_from: '2026-10-01', order_date_to: '2026-10-31' })
  })

  it('Của tôi is disabled for an account with no employee record', () => {
    useAuthStore.setState({ user: { id: 8, email: 'kho@dego.vn', full_name: 'kho@dego.vn', employee_id: 0, permissions: {} } })
    build()

    expect(chip('Của tôi')).toBeDisabled()
  })
})

describe('PurchaseOrderListPage — nút Xóa lọc và câu bảng rỗng', () => {
  it('clears EVERY quick filter, chip flags included, in one go', async () => {
    //  Lỗi cũ (kh-NT2-2): mười hai setter gọi liền nhau, chỉ ô cuối bị xóa.
    build(
      '/procurement/purchase-orders?company_id=1&nspt_id=9&status=approved&is_urgent=true&missing_docs=1&order_date_from=2026-10-01&order_date_to=2026-10-31&invoice_no=77',
    )
    const sheetTrigger = screen
      .getAllByRole('button', { name: 'Bộ lọc' })
      .find((button) => button.getAttribute('data-slot') === 'sheet-trigger')
    if (!sheetTrigger) throw new Error('Không thấy nút mở tờ lọc')
    fireEvent.click(sheetTrigger)
    fireEvent.click(await screen.findByRole('button', { name: 'Xóa lọc' }))

    const call = lastCall()
    expect(call.company_id).toBeUndefined()
    expect(call.nspt_id).toBeUndefined()
    expect(call.status).toBeUndefined()
    expect(call.is_urgent).toBeUndefined()
    expect(call.document_status__in).toBeUndefined()
    expect(call.order_date_from).toBeUndefined()
    //  Ô số hóa đơn là ô GÕ (trễ 350ms): ô theo URL ngay, tham số gửi đi theo sau một nhịp.
    await waitFor(() => expect(lastCall().invoice_no).toBeUndefined())
  })

  it('says the table is empty BECAUSE of the filters when any filter is on', () => {
    //  Bộ lọc nay còn được khôi phục âm thầm từ bản nhớ khi mở lại màn — câu chung
    //  "không tìm thấy" làm người ta tưởng mất dữ liệu.
    build('/procurement/purchase-orders?status=approved')

    expect(screen.getAllByText(/khớp bộ lọc đang chọn/).length).toBeGreaterThan(0)
  })

  it('keeps the plain empty sentence when nothing is filtered', () => {
    build()

    expect(screen.queryByText(/khớp bộ lọc đang chọn/)).toBeNull()
    expect(screen.getAllByText('Không tìm thấy đơn mua hàng nào.').length).toBeGreaterThan(0)
  })

  it('does not count a chip that is greyed out by an OR advanced filter', () => {
    //  Chip mờ không lọc gì; đếm nó thì huy hiệu báo đang lọc trong khi không phải.
    build('/procurement/purchase-orders?missing_docs=1&code__contains=A&pr_code__contains=B&conjunction=or')
    const sheetTrigger = screen
      .getAllByRole('button', { name: 'Bộ lọc' })
      .find((button) => button.getAttribute('data-slot') === 'sheet-trigger')
    if (!sheetTrigger) throw new Error('Không thấy nút mở tờ lọc')
    fireEvent.click(sheetTrigger)

    //  Không ô lọc nhanh nào đang bật → tờ lọc không có nút Xóa lọc, không có huy hiệu.
    expect(screen.queryByRole('button', { name: 'Xóa lọc' })).toBeNull()
  })
})

describe('PurchaseOrderListPage — cột Phòng xử lý (bao-CR-705)', () => {
  function row(id: number, handler: string | undefined) {
    return {
      id, code: `PO0${id}`, misa_code: '', pr_code: '', survey_code: '', company_id: 1,
      supplier_code: 'NCC', supplier_name: 'Nhà cung cấp', department: 'Dego Organic', nspt: '',
      order_date: '2026-10-31', is_urgent: false, order_type: 1, status: 'approved',
      document_status: '', note: '', created_at: '2026-10-31T08:00:00', amount: 0,
      handler_dept_id: 5, handler_dept_name: handler, approver_name: 'Đoàn Minh Khôi',
      company_name: 'CÔNG TY TNHH DEGO HOLDING', created_by_name: 'Trần Diễm Phương',
    }
  }

  it('shows the handling department as its own column, visible without touching the Cột menu', () => {
    listItems.push(row(1, 'Dego Organic'), row(2, 'Sản xuất -Thu mua'))
    build()
    expect(screen.getByRole('columnheader', { name: /Phòng xử lý/ })).toBeInTheDocument()
    expect(screen.getByText('Sản xuất -Thu mua')).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: /Trưởng phòng phê duyệt/ })).toBeInTheDocument()
    expect(screen.getAllByText('Đoàn Minh Khôi').length).toBeGreaterThan(0)
  })

  it('keeps the extra columns hidden until the user ticks them in the Cột menu', () => {
    listItems.push(row(1, 'Dego Organic'))
    build()
    expect(screen.queryByRole('columnheader', { name: /Công ty nhận hóa đơn/ })).not.toBeInTheDocument()
    expect(screen.queryByText('Trần Diễm Phương')).not.toBeInTheDocument()
  })

  it('does not switch the extra columns on for someone whose layout was saved before CR-705', () => {
    //  Bố cục lưu kiểu cũ (chưa có knownColumns): luật cũ sẽ bật sẵn mọi cột mới thêm.
    localStorage.setItem(
      'erp.table.procurement.purchase-orders',
      JSON.stringify({ hiddenColumns: [], columnWidths: { code: 160 } }),
    )
    listItems.push(row(1, 'Dego Organic'))
    build()
    expect(screen.queryByRole('columnheader', { name: /Công ty nhận hóa đơn/ })).not.toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: /Phòng xử lý/ })).toBeInTheDocument()
  })

  it('leaves the cell blank instead of printing undefined when the server sends no name', () => {
    listItems.push(row(3, undefined))
    build()
    expect(screen.queryByText('undefined')).not.toBeInTheDocument()
  })
})
