import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { ListParams } from '@/shared/types/api'
import { SurveyListPage } from './survey-list-page'
import type { Survey } from '../types/purchase-document'

//  Chặn ở tầng HOOK dữ liệu chứ không ở `@/core/api`: màn này phải bắt được BỘ
//  THAM SỐ nó gửi đi, mà tham số đó chỉ hiện nguyên vẹn ở đầu vào của hook.
const listCalls: ListParams[] = []

vi.mock('../hooks/use-purchase-documents', () => ({
  useSurveys: (params: ListParams) => {
    listCalls.push(params)
    return { data: { total: rows.length, items: rows }, isLoading: false, isError: false }
  },
}))

vi.mock('../hooks/use-purchase-request-support', () => ({
  usePurchaseRequestItemGroups: () => ({
    data: { total: 2, items: [{ id: 1, name: 'Bao bì' }, { id: 2, name: 'Nguyên liệu' }] },
  }),
}))

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => true, canAccess: () => true }),
}))

const rows: Survey[] = [
  {
    id: 1,
    code: 'KS-0001',
    survey_type: 'product',
    sr_code: 'YCBG-0001',
    pr_code: '',
    item_group: 'Bao bì',
    main_content: 'Thùng carton 5 lớp',
    item_code: 'SP-001',
    item_name: 'Thùng carton',
    nspt: 'NV01',
    status: 'approved',
    created_at: '2026-08-03 09:00:00',
  },
]

function build(url = '/procurement/surveys') {
  //  `DataTable` gọi `useQueryClient` cho nút Tải lại — vẫn phải có provider dù
  //  mọi hook dữ liệu của màn này đã bị chặn.
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[url]}>
        <SurveyListPage />
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

/**
 * bao-CR-447 — ô NHÓM HÀNG.
 *
 * Bản v1 có ô này trên thanh lọc nhanh, v2 thì không: người dùng muốn xem "khảo
 * sát của nhóm Bao bì" phải mở *Bộ lọc điều kiện* rồi dựng một dòng điều kiện —
 * ba thao tác cho một câu hỏi hỏi hằng ngày.
 */
describe('SurveyListPage — ô Nhóm hàng', () => {
  it('bày ô Nhóm hàng trên thanh công cụ', () => {
    build()

    //  Nhãn nằm ở thẻ BỌC: `SearchSelect` không spread prop lạ nên `aria-label`
    //  truyền thẳng vào component sẽ lọt `tsc` rồi rơi vào hư không.
    expect(screen.getAllByLabelText('Lọc theo nhóm hàng').length).toBeGreaterThan(0)
  })

  it('sends item_group as the group NAME — cột `Survey.item_group` lưu tên', () => {
    //  Gửi id xuống thì `apply_filters` so `item_group LIKE %1%`: không dòng nào
    //  khớp, bảng rỗng mà không chỗ nào báo.
    build('/procurement/surveys?item_group=Bao bì')

    expect(lastCall().item_group).toBe('Bao bì')
  })

  it('sends no item_group when nothing is picked', () => {
    build()

    expect(lastCall().item_group).toBeUndefined()
  })

  it('treats the sentinel "all" as no filter, not as a group named "all"', () => {
    build('/procurement/surveys?item_group=all')

    expect(lastCall().item_group).toBeUndefined()
  })

  it('keeps the other quick filters while a group is picked', () => {
    build('/procurement/surveys?item_group=Bao bì&status=approved&survey_type=product')

    expect(lastCall()).toMatchObject({
      item_group: 'Bao bì',
      status: 'approved',
      survey_type: 'product',
    })
  })
})

describe('SurveyListPage — ô tìm kiếm', () => {
  it('sends the keyword as `code` — backend gộp code/q/search/product_code vào một câu tìm', () => {
    //  `product_code` KHÔNG còn là tham số riêng của màn này: backend đọc cả bốn
    //  khóa vào cùng một câu tìm đa trường, nên ô tìm đã gánh luôn phần mã SP.
    build('/procurement/surveys?q=carton')

    expect(lastCall().code).toBe('carton')
    expect(lastCall().product_code).toBeUndefined()
  })
})
