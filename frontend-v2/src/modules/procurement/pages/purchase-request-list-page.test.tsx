import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

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
