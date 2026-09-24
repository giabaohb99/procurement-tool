import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

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

//  bao-CR-442: nút "Xuất Excel" gác bằng quyền `export` của ĐMH HOẶC của YCMH,
//  nên hai cờ tách riêng để bắt được đúng phép HOẶC đó.
let canExportPurchaseOrder = true
let canExportPurchaseRequest = false
let canReadSupplier = true

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (entity: string, action: string) => {
      if (entity === 'supplier' && action === 'read') return canReadSupplier
      if (action !== 'export') return true
      if (entity === 'purchase_order') return canExportPurchaseOrder
      if (entity === 'purchase_request') return canExportPurchaseRequest
      return false
    },
    canAccess: () => true,
  }),
}))

const downloadFile = vi.fn()

vi.mock('@/core/api/download-file', () => ({
  downloadFile: (...args: unknown[]) => downloadFile(...args),
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
    price: 1000,
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
  downloadFile.mockReset()
  canExportPurchaseOrder = true
  canExportPurchaseRequest = false
  canReadSupplier = true
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

    //  bao-CR-423: hai ô này chọn được nhiều giá trị nên gửi đi là CHUỖI nối
    //  bằng dấu phẩy, kể cả khi mới chọn một — `read_multi_param` bên backend
    //  đọc được cả hai dạng.
    expect(lastCall()).toMatchObject({
      company_id: '7',
      status: 'partial',
      order_date_from: '2026-08-01',
    })
  })

  it('joins several picks of one filter box into a single comma-joined param', () => {
    //  Nhiều giá trị trong CÙNG một ô = HOẶC; hai ô khác nhau vẫn là VÀ.
    build('/procurement/purchase-progress?company_id=7,9&status=partial,ordered')

    expect(lastCall()).toMatchObject({ company_id: '7,9', status: 'partial,ordered' })
  })

  it('sends no param for a filter box with nothing picked', () => {
    build('/procurement/purchase-progress?status=')

    expect(lastCall().status).toBeUndefined()
    expect(lastCall().company_id).toBeUndefined()
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

describe('PurchaseProgressPage — căn cứ quy đổi của cột tiền (bao-CR-439)', () => {
  //  Từ bao-CR-437 mọi cột "Thành tiền" trên màn này đã QUY ĐỔI về đồng, trong khi ô
  //  Đơn giá ngay bên trái vẫn là số nguyên tệ in trên hóa đơn nhà cung cấp. Hai ô cạnh
  //  nhau mang hai loại tiền mà không ô nào nói ra thì người đọc nhân tay và ra một con
  //  số thứ ba — đúng câu hỏi "sao số này khác số kia" mà CR này sinh ra để trả lời.
  const fxRow = {
    po_id: 2,
    po_code: 'PO-0002',
    company_id: 0,
    order_date: '2026-08-06',
    product_code: 'SP-02',
    product_name: 'Màng PE nhập khẩu',
    price: 4.85,
    currency: 'CNY',
    exchange_rate: 3.62,
    order_amount: 155_117_000,
    delivery_no: 1,
  } as PurchaseProgressRow

  beforeEach(() => {
    rows.push(fxRow)
  })

  afterEach(() => {
    rows.pop()
  })

  it('puts both conversion-basis columns on the table, not behind the "Cột" menu', () => {
    build()

    expect(screen.getByText('Đồng tiền')).toBeInTheDocument()
    expect(screen.getByText('Tỷ giá')).toBeInTheDocument()
    expect(screen.getByText('CNY')).toBeInTheDocument()
    expect(screen.getByText('3,62')).toBeInTheDocument()
  })

  it('stamps the currency code on a foreign-currency unit price and leaves a dong one bare', () => {
    build()

    expect(screen.getByText('4,85 CNY')).toBeInTheDocument()
    //  Gần hết đơn là VND: gắn đuôi vào mọi dòng thì cột dài thêm mà chẳng nói gì mới.
    expect(screen.getByText('1.000')).toBeInTheDocument()
    expect(screen.queryByText('1.000 VND')).toBeNull()
  })
})

describe('PurchaseProgressPage — tình trạng nhận (bao-CR-442)', () => {
  it('forwards the pick as recv_state — the one filter that asks about the total received', () => {
    build('/procurement/purchase-progress?recv_state=under')

    expect(lastCall().recv_state).toBe('under')
  })

  it('sends nothing when the box is left at "Tất cả"', () => {
    //  "all" là mốc của giao diện, không phải một giá trị backend hiểu: gửi lên
    //  thì `_build_query` so `recv_state == "all"` không trúng nhánh nào và bộ
    //  lọc coi như bị bỏ qua — im lặng, đúng kiểu khó tìm nhất.
    build('/procurement/purchase-progress?recv_state=all')

    expect(lastCall().recv_state).toBeUndefined()
  })

  it('shows the box with the wording of the bản cũ so the two screens answer the same question', () => {
    build()

    expect(screen.getByText('Tất cả tình trạng nhận')).toBeInTheDocument()
  })
})

describe('PurchaseProgressPage — bộ lọc điều kiện (bao-CR-442)', () => {
  it('forwards a conditional-filter param read from the URL', () => {
    //  Khóa phải khớp `_cond_map()` bên backend; sai một chữ thì backend bỏ qua
    //  IM LẶNG và người dùng vẫn thấy nguyên danh sách cũ.
    build('/procurement/purchase-progress?currency__eq=CNY')

    expect(lastCall().currency__eq).toBe('CNY')
  })

  it('drops the supplier conditions when the user cannot read suppliers', () => {
    //  Backend gỡ hẳn cụm NCC khỏi map khi thiếu `supplier.read` — lọc rồi đếm
    //  số dòng còn lại là mò ra được tên nhà cung cấp.
    canReadSupplier = false
    build('/procurement/purchase-progress?supplier_name__contains=Minh&currency__eq=CNY')

    expect(lastCall().supplier_name__contains).toBeUndefined()
    expect(lastCall().currency__eq).toBe('CNY')
  })
})

describe('PurchaseProgressPage — xuất Excel (bao-CR-442)', () => {
  it('hides the button when the user can export neither ĐMH nor YCMH', () => {
    canExportPurchaseOrder = false
    canExportPurchaseRequest = false
    build()

    expect(screen.queryByRole('button', { name: /Xuất Excel/ })).toBeNull()
  })

  it('shows the button on the YCMH permission alone — a row joins both chứng từ', () => {
    canExportPurchaseOrder = false
    canExportPurchaseRequest = true
    build()

    expect(screen.getByRole('button', { name: /Xuất Excel/ })).toBeInTheDocument()
  })

  it('exports with the filters on screen but without the paging', async () => {
    //  Gửi kèm `page`/`page_size` thì tệp chỉ có đúng trang đang xem — người
    //  dùng lọc ra 900 dòng, bấm xuất, mở tệp ra thấy 20 dòng mà không báo gì.
    build('/procurement/purchase-progress?company_id=7&recv_state=full&date_from=2026-08-01')

    await userEvent.click(screen.getByRole('button', { name: /Xuất Excel/ }))

    await waitFor(() => expect(downloadFile).toHaveBeenCalledTimes(1))
    const [url, filename, params] = downloadFile.mock.calls[0] as [
      string,
      string,
      Record<string, unknown>,
    ]
    expect(url).toBe('/api/purchase-progress/export/xlsx')
    expect(filename).toBe('tien-do-mua-hang.xlsx')
    expect(params).toMatchObject({
      company_id: '7',
      recv_state: 'full',
      order_date_from: '2026-08-01',
    })
    expect(params.page).toBeUndefined()
    expect(params.page_size).toBeUndefined()
  })

  it('asks only for the columns still on the table', async () => {
    build()

    await userEvent.click(screen.getByRole('button', { name: /Xuất Excel/ }))

    await waitFor(() => expect(downloadFile).toHaveBeenCalledTimes(1))
    const params = downloadFile.mock.calls[0][2] as Record<string, unknown>
    const cols = String(params.cols).split(',')
    expect(cols).toContain('po_code')
    //  Khóa cột của bảng trùng khóa cột trong `purchase_progress/export.py`, nên
    //  gửi thẳng được — cột `defaultHidden` không nằm trong danh sách này.
    expect(cols).not.toContain('misa_code')
  })
})
