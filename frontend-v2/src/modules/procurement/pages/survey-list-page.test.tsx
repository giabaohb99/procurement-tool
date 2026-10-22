import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/core/auth/auth-store'
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
  sessionStorage.clear()
  useAuthStore.setState({ user: null })
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

/**
 * kh-NT2-2 — chip lọc nhanh (doc `erp/nen-tang/14` §2.4).
 *
 * Phiếu khảo sát không có cột ngày lọc được ở máy chủ nên KHÔNG có chip *Tháng này*.
 */
describe('SurveyListPage — chip lọc nhanh', () => {
  beforeEach(() => {
    useAuthStore.setState({
      user: { id: 7, email: 'bao@dego.vn', full_name: 'Huỳnh Gia Bảo', employee_id: 9, emp_code: 'NSU209', permissions: {} },
    })
  })

  afterEach(() => {
    useAuthStore.setState({ user: null })
  })

  function chip(name: string) {
    return screen.getAllByRole('button', { name })[0]
  }

  it('Của tôi filters by the NSPT NAME — `Survey.nspt` stores the creator name, not a code', () => {
    build()
    fireEvent.click(chip('Của tôi'))

    expect(lastCall().nspt).toBe('Huỳnh Gia Bảo')
  })

  it('Chờ xử lý asks for surveys not yet approved', () => {
    build()
    fireEvent.click(chip('Chờ xử lý'))

    expect(lastCall().status__in).toBe('draft,submitted')
  })

  it('has no Tháng này chip — the server cannot filter surveys by date', () => {
    build()

    expect(screen.queryByRole('button', { name: 'Tháng này' })).toBeNull()
  })
})

describe('SurveyListPage — chip loại khảo sát và nút Xóa lọc', () => {
  beforeEach(() => {
    useAuthStore.setState({
      user: { id: 7, email: 'bao@dego.vn', full_name: 'Huỳnh Gia Bảo', employee_id: 9, emp_code: 'NSU209', permissions: {} },
    })
  })

  function chip(name: string) {
    return screen.getAllByRole('button', { name })[0]
  }

  it('Khảo sát NCC and Khảo sát SP write into the survey type box', () => {
    build()
    fireEvent.click(chip('Khảo sát NCC'))
    expect(lastCall().survey_type).toBe('supplier')

    fireEvent.click(chip('Khảo sát SP'))
    expect(lastCall().survey_type).toBe('product')
    expect(chip('Khảo sát NCC')).toHaveAttribute('aria-pressed', 'false')

    fireEvent.click(chip('Khảo sát SP'))
    expect(lastCall().survey_type).toBeUndefined()
  })

  it('clears the quick filters AND the advanced conditions in one go', async () => {
    //  Lỗi cũ: `filter.reset()` gọi sau cùng chép trả các ô vừa xóa (`preserveParams`).
    build('/procurement/surveys?status=approved&survey_type=product&item_group=Bao%20b%C3%AC&nspt=NV01&pending=1&sr_code__contains=YCBG')
    const sheetTrigger = screen
      .getAllByRole('button', { name: 'Bộ lọc' })
      .find((button) => button.getAttribute('data-slot') === 'sheet-trigger')
    if (!sheetTrigger) throw new Error('Không thấy nút mở tờ lọc')
    fireEvent.click(sheetTrigger)
    fireEvent.click(await screen.findByRole('button', { name: 'Xóa lọc' }))

    const call = lastCall()
    expect(call.status).toBeUndefined()
    expect(call.survey_type).toBeUndefined()
    expect(call.item_group).toBeUndefined()
    expect(call.nspt).toBeUndefined()
    expect(call.status__in).toBeUndefined()
    expect(call.sr_code__contains).toBeUndefined()
  })
})
