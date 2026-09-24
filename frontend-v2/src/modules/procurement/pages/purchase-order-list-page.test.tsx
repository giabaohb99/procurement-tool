import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { ListParams } from '@/shared/types/api'
import { PurchaseOrderListPage } from './purchase-order-list-page'

//  Chặn ở tầng HOOK dữ liệu chứ không ở `@/core/api`: màn này phải bắt được BỘ
//  THAM SỐ nó gửi đi, mà hai ô lọc của bao-CR-443 (`item_group`, `invoice_no`)
//  chạy trên bảng DÒNG và bảng LẦN GIAO nên chỉ nhìn thấy ở đây.
const listCalls: ListParams[] = []

vi.mock('../hooks/use-purchase-documents', () => ({
  usePurchaseOrders: (params: ListParams) => {
    listCalls.push(params)
    return { data: { total: 0, items: [] }, isLoading: false, isError: false }
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
  localStorage.clear()
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
