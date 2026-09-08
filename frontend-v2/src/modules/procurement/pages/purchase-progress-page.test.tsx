import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { ListParams } from '@/shared/types/api'
import { PurchaseProgressPage } from './purchase-progress-page'
import type { PurchaseProgressRow } from '../types/purchase-progress'

//  Chặn ở tầng HOOK dữ liệu chứ không ở `@/core/api`: màn này phải bắt được BỘ
//  THAM SỐ nó gửi đi (`order_date_from` / `received_date_from`), mà tham số đó
//  chỉ hiện nguyên vẹn ở đầu vào của hook.
const listCalls: ListParams[] = []

vi.mock('../hooks/use-purchase-documents', () => ({
  usePurchaseProgress: (params: ListParams) => {
    listCalls.push(params)
    return { data: { total: rows.length, items: rows, show_supplier: true }, isLoading: false, isError: false }
  },
}))

vi.mock('@/modules/hr/hooks/use-companies', () => ({
  useCompanies: () => ({ data: { total: 1, items: [{ id: 7, name: 'Công ty Dego Cần Thơ' }] } }),
}))

vi.mock('@/modules/hr/hooks/use-departments', () => ({
  useDepartments: () => ({ data: { total: 1, items: [{ id: 3, name: 'Phòng Sản xuất' }] } }),
}))

const rows: PurchaseProgressRow[] = [
  {
    po_id: 1,
    po_code: 'PO-0001',
    company_id: 7,
    order_date: '2026-08-05',
    received_date: '2026-09-02',
    product_code: 'SP-01',
    product_name: 'Thùng carton 3 lớp',
    delivery_no: 1,
  } as PurchaseProgressRow,
]

function build(url = '/procurement/purchase-progress') {
  //  `DataTable` gọi `useQueryClient` cho nút Tải lại — vẫn phải có provider dù
  //  mọi hook dữ liệu của màn này đã bị chặn.
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[url]}>
        <PurchaseProgressPage />
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

describe('PurchaseProgressPage — khoảng ngày', () => {
  it('sends the range as order dates by default — that is the mốc of the chứng từ', () => {
    build('/procurement/purchase-progress?date_from=2026-08-01&date_to=2026-08-31')

    expect(lastCall()).toMatchObject({
      order_date_from: '2026-08-01',
      order_date_to: '2026-08-31',
    })
    expect(lastCall().received_date_from).toBeUndefined()
  })

  it('switches to the received dates when the user picks that mốc', () => {
    //  Một dòng ở đây là MỘT LẦN GIAO: đơn đặt tháng 8 giao làm nhiều đợt sang
    //  tháng 9, nên hỏi nhầm mốc là ra tập khác hẳn.
    build('/procurement/purchase-progress?date_field=received&date_from=2026-09-01&date_to=2026-09-30')

    expect(lastCall()).toMatchObject({
      received_date_from: '2026-09-01',
      received_date_to: '2026-09-30',
    })
    expect(lastCall().order_date_from).toBeUndefined()
  })

  it('accepts a half-open range — "từ 01/08 tới nay" is a real question', () => {
    build('/procurement/purchase-progress?date_from=2026-08-01')

    expect(lastCall().order_date_from).toBe('2026-08-01')
    expect(lastCall().order_date_to).toBeUndefined()
  })

  it('sends no date param at all when the range is empty', () => {
    //  Chuỗi rỗng gửi lên là backend so `col >= ""` — đúng với mọi dòng CÓ ngày
    //  và loại sạch dòng chưa có ngày. Bảng rỗng ngay lúc mở màn.
    build('/procurement/purchase-progress?date_from=&date_to=')

    expect(lastCall().order_date_from).toBeUndefined()
    expect(lastCall().order_date_to).toBeUndefined()
    expect(lastCall().received_date_from).toBeUndefined()
  })

  it('keeps the other filters while a range is active', () => {
    build('/procurement/purchase-progress?company_id=7&status=partial&date_from=2026-08-01')

    expect(lastCall()).toMatchObject({
      company_id: 7,
      status: 'partial',
      order_date_from: '2026-08-01',
    })
  })

  it('shows both controls on the toolbar', () => {
    build()

    expect(screen.getByText('Theo ngày ĐH')).toBeInTheDocument()
    expect(screen.getByText('Từ ngày – tới ngày')).toBeInTheDocument()
  })
})

describe('PurchaseProgressPage — cột chữ đọc đủ', () => {
  //  Khách nêu 31/08/2026: "cho show full ra chứ đừng có …". Xuống dòng là hiệu
  //  ứng CSS, jsdom không đo được, nên đành khẳng định theo class — đây là chỗ
  //  DUY NHẤT trong bộ test này làm vậy, vì class CHÍNH LÀ hành vi.
  //
  //  Bắt hai lối hỏng cùng lúc: bỏ `wrap` ở cột (lớp bọc quay về `truncate`),
  //  và gắn lại `truncate` trong `cell` (class ô con thắng lớp bọc của bảng,
  //  `wrap` thành vô hiệu mà nhìn code vẫn tưởng đang bật).
  function cellOf(text: string) {
    const cell = screen.getByText(text).closest('td')
    if (!cell) throw new Error(`Không tìm thấy ô chứa "${text}"`)
    return cell
  }

  it('lets the long text columns wrap instead of cutting them with "…"', () => {
    build()

    for (const text of ['PO-0001', 'Thùng carton 3 lớp', 'Công ty Dego Cần Thơ']) {
      expect(cellOf(text).querySelector('.truncate')).toBeNull()
      expect(cellOf(text).querySelector('.whitespace-normal')).not.toBeNull()
    }
  })

  it('keeps the number and date columns on one line so the rows stay even', () => {
    build()

    // Cột ngày để nguyên `truncate`: cho xuống dòng thì hàng cao lệch nhau mà
    // chẳng đọc thêm được chữ nào.
    expect(cellOf('05/08/2026').querySelector('.truncate')).not.toBeNull()
  })
})
