import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { ListParams } from '@/shared/types/api'
import { PayableListPage } from './payable-list-page'
import type { Payable, PayableSummary } from '../types/payable'

//  Chặn ở tầng HOOK dữ liệu chứ không ở `@/core/api`: màn này còn phải bắt được
//  BỘ THAM SỐ nó gửi đi (`due_from` / `incur_from` / `year`), mà tham số đó chỉ
//  hiện nguyên vẹn ở đầu vào của hook.
const listCalls: ListParams[] = []

// bao-CR-414 GĐ4: thẻ tổng hợp có hai bộ số (phần của tôi + tổng nợ NCC không gác phạm
// vi). Mặc định là người phạm vi toàn bộ — backend gửi `partial: false`.
let summaryData: PayableSummary = { total: 0, paid: 0, remaining: 0, overdue: 0, partial: false }

// bao-CR-275: bắt tham số nút "Xuất Excel" gửi xuống — ids tick chọn + cols theo
// cột đang hiện. `vi.hoisted` vì vi.mock được kéo lên trên mọi khai báo const.
const { downloadFileMock } = vi.hoisted(() => ({ downloadFileMock: vi.fn() }))

vi.mock('@/core/api/download-file', () => ({ downloadFile: downloadFileMock }))

vi.mock('../hooks/use-payables', () => ({
  usePayables: (params: ListParams) => {
    listCalls.push(params)
    return { data: { total: rows.length, items: rows }, isLoading: false, isError: false }
  },
  usePayableSummary: () => ({ data: summaryData, isLoading: false }),
  // CR-268: dialog cấn trừ tiền trả trước mount sẵn (đóng) trên trang — thiếu
  // export này là cả trang nổ ngay lúc render, 10 test không liên quan đỏ theo.
  useOffsetPrepay: () => ({ mutateAsync: vi.fn(), isPending: false }),
}))

vi.mock('@/modules/hr/hooks/use-companies', () => ({
  useCompanies: () => ({ data: { total: 1, items: [{ id: 7, name: 'Công ty Dego Cần Thơ' }] } }),
}))

// ai-CR-017: ô "Nhà cung cấp" mới bù ra thanh lọc ngoài cần danh mục NCC.
vi.mock('@/modules/production/hooks/use-suppliers', () => ({
  useSuppliers: () => ({
    data: { total: 1, items: [{ code: 'NCC-1', name: 'Nhà cung cấp 1' }] },
  }),
}))

let canCreatePayment = true
let canExportPayable = true
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (entity: string, action: string) => {
      if (entity === 'payment_request') return canCreatePayment
      if (entity === 'payable' && action === 'export') return canExportPayable
      return true
    },
    canAccess: () => true,
  }),
}))

function payable(over: Partial<Payable> & { id: number }): Payable {
  return {
    company_id: 7,
    supplier_code: `NCC-${over.id}`,
    supplier_name: `Nhà cung cấp ${over.id}`,
    source_type: 'goods',
    po_id: 100 + over.id,
    po_code: `PO-${over.id}`,
    invoice_no: `HD-${over.id}`,
    incur_date: '2026-07-01',
    due_date: '2026-08-15',
    created_at: '2026-07-01 09:00:00',
    amount: 1000,
    vat: 80,
    total: 1080,
    paid_amount: 0,
    remaining: 1080,
    status: 'unpaid',
    status_label: 'Chưa trả',
    aging: 'Chưa đến hạn',
    ...over,
  } as Payable
}

//  Bốn dòng: hai dòng tick được, một dòng THIẾU số hóa đơn, một dòng ĐÃ tất toán.
const rows: Payable[] = [
  payable({
    id: 1,
    supplier_name: 'Công ty TNHH Thương mại Dịch vụ Xuất nhập khẩu Phương Nam',
    supplier_code: 'NCC-A',
  }),
  payable({ id: 2, supplier_code: 'NCC-A' }),
  payable({ id: 3, invoice_no: '' }),
  payable({ id: 4, status: 'paid', status_label: 'Đã trả', paid_amount: 1080, remaining: 0 }),
]

function build(url = '/finance/payables') {
  //  `DataTable` gọi `useQueryClient` cho nút Tải lại — vẫn phải có provider dù
  //  mọi hook dữ liệu của màn này đã bị chặn.
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[url]}>
        <PayableListPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

/** Ô tick ở TIÊU ĐỀ cột — cái "tích một cái là chọn hết". */
function headerCheckbox() {
  return screen.getByRole('checkbox', { name: /khoản trong trang/ })
}

function rowCheckboxes() {
  return screen.getAllByRole('checkbox', { name: 'Chọn khoản nợ này để lên đề nghị thanh toán' })
}

function submitButton() {
  return screen.getByRole('button', { name: /Tạo đề nghị thanh toán/ })
}

/**
 * Nút **Bộ lọc** của khổ RỘNG (popover gộp khoảng tiền + bộ lọc điều kiện).
 *
 * ⚠️ Trang dựng HAI nút cùng tên: một của tờ trượt khổ hẹp (`QuickFilterSheet`,
 * mang `md:hidden`) và một của popover khổ rộng (mang `max-md:hidden`). jsdom
 * không áp CSS nên cả hai cùng nằm trong cây — bản khổ rộng dựng SAU trong
 * JSX nên là nút cuối. Cùng khuôn `survey-report-page.test.tsx`.
 */
async function desktopFilterTrigger() {
  const triggers = await screen.findAllByRole('button', { name: 'Bộ lọc' })
  return triggers[triggers.length - 1]
}

beforeEach(() => {
  listCalls.length = 0
  canCreatePayment = true
  canExportPayable = true
  downloadFileMock.mockClear()
  localStorage.clear()
  summaryData = { total: 0, paid: 0, remaining: 0, overdue: 0, partial: false }
})

describe('PayableListPage — thẻ tổng hợp theo phạm vi (bao-CR-414 GĐ4)', () => {
  it('shows only the four original cards when the viewer sees everything', () => {
    summaryData = {
      total: 1700,
      paid: 0,
      remaining: 1700,
      overdue: 0,
      all: { total: 1700, paid: 0, remaining: 1700, overdue: 0 },
      partial: false,
    }
    build()

    expect(screen.getByText('Tổng nợ', { selector: 'p' })).toBeInTheDocument()
    expect(screen.queryByText(/Phần của tôi/)).not.toBeInTheDocument()
    expect(screen.queryByText(/Tổng nợ NCC/)).not.toBeInTheDocument()
  })

  it('splits the first card into supplier total and my share when the viewer sees a part', () => {
    summaryData = {
      total: 1000,
      paid: 0,
      remaining: 1000,
      overdue: 0,
      all: { total: 1700, paid: 0, remaining: 1700, overdue: 0 },
      partial: true,
    }
    build()

    //  Hai con số phải là HAI ô khác nhau: 1.700 là nợ của công ty với NCC, 1.000 là
    //  phần phòng tôi mua. Gộp làm một là người xem tưởng công ty chỉ nợ 1.000.
    //  Bảng bên dưới cũng có cột "Tổng nợ" nên chỉ soi các nhãn `<p>` của thẻ tổng hợp.
    expect(screen.getByText(/Tổng nợ NCC/, { selector: 'p' })).toBeInTheDocument()
    expect(screen.getByText('1.700', { selector: 'p' })).toBeInTheDocument()
    expect(screen.getByText('Phần của tôi', { selector: 'p' })).toBeInTheDocument()
    expect(screen.getAllByText('1.000', { selector: 'p' }).length).toBeGreaterThanOrEqual(1)
    expect(screen.queryByText('Tổng nợ', { selector: 'p' })).not.toBeInTheDocument()
  })

  it('does not split the cards when the old backend omits the partial flag', () => {
    summaryData = { total: 5, paid: 0, remaining: 5, overdue: 0 }
    build()

    expect(screen.getByText('Tổng nợ', { selector: 'p' })).toBeInTheDocument()
    expect(screen.queryByText('Phần của tôi')).not.toBeInTheDocument()
  })
})

describe('PayableListPage — chọn hết trong trang', () => {
  it('ticks every eligible row on the page in one click, skipping the ineligible ones', async () => {
    const user = userEvent.setup()
    build()

    await user.click(headerCheckbox())

    // 4 dòng nhưng chỉ 2 dòng đủ điều kiện: dòng thiếu số HĐ và dòng đã tất toán
    // KHÔNG được tick hộ — backend sẽ từ chối chúng.
    expect(submitButton()).toHaveTextContent('2 khoản')
    expect(submitButton()).toHaveTextContent('1 NCC')
  })

  it('leaves the ineligible rows disabled so they cannot be ticked at all', () => {
    build()
    const boxes = rowCheckboxes()

    expect(boxes[0]).toBeEnabled()
    expect(boxes[1]).toBeEnabled()
    expect(boxes[2]).toBeDisabled() // chưa có số hóa đơn
    expect(boxes[3]).toBeDisabled() // đã tất toán
  })

  it('shows the half-state when only part of the page is ticked', async () => {
    const user = userEvent.setup()
    build()

    await user.click(rowCheckboxes()[0])

    // `mixed` = đang chọn một phần. Hiện dấu tick đầy ở đây là nói dối người dùng
    // rằng cả trang đã được chọn.
    expect(headerCheckbox()).toHaveAttribute('aria-checked', 'mixed')
  })

  it('clears the page again on the second click', async () => {
    const user = userEvent.setup()
    build()

    await user.click(headerCheckbox())
    expect(headerCheckbox()).toHaveAttribute('aria-checked', 'true')

    await user.click(headerCheckbox())

    expect(submitButton()).toBeDisabled()
    expect(headerCheckbox()).toHaveAttribute('aria-checked', 'false')
  })

  it('hides the whole select column when the user cannot raise a payment request', () => {
    canCreatePayment = false
    build()

    expect(screen.queryByRole('checkbox', { name: /khoản trong trang/ })).not.toBeInTheDocument()
    expect(screen.queryAllByRole('checkbox')).toHaveLength(0)
  })
})

describe('PayableListPage — xuất Excel (bao-CR-275)', () => {
  function exportButton() {
    return screen.getByRole('button', { name: /Xuất Excel/ })
  }

  it('translates the visible screen columns into file column keys, dropping the screen-only ones', async () => {
    const user = userEvent.setup()
    build()

    await user.click(exportButton())

    //  Cột tick chọn + cột cấn trừ không có mặt trong file; ba cột ẩn mặc định
    //  (Ngày ghi sổ / tiền trước VAT / VAT) không được lọt vào. bao-CR-306: bảng
    //  dịch nay 1-1 — `incur_date` xuất đúng `incur_date`, có thêm `invoice_date`;
    //  hồi map `incur_date -> created_at` file xuất nhầm giờ ghi sổ dưới nhãn
    //  "Ngày phát sinh", đừng quay lại bản map đó.
    expect(downloadFileMock).toHaveBeenCalledWith(
      '/api/payables/export/xlsx',
      'cong-no-phai-tra.xlsx',
      expect.objectContaining({
        cols: [
          'supplier_name',
          'supplier_code',
          'source_type',
          'company',
          'po_code',
          'invoice_no',
          'invoice_date',
          'incur_date',
          'due_date',
          'aging',
          'total',
          'paid_amount',
          'remaining',
          'status',
        ].join(','),
      }),
    )
    //  Không tick gì thì KHÔNG gửi `ids` — gửi chuỗi rỗng là backend hiểu nhầm
    //  thành "tick rỗng" và trả về file trắng.
    expect(downloadFileMock.mock.calls[0][2].ids).toBeUndefined()
  })

  it('sends only the ticked rows as ids and keeps the active filter params', async () => {
    const user = userEvent.setup()
    build('/finance/payables?year=2025')

    await user.click(rowCheckboxes()[0])
    await user.click(rowCheckboxes()[1])
    await user.click(exportButton())

    expect(downloadFileMock.mock.calls[0][2]).toMatchObject({ ids: '1,2', year: '2025' })
  })

  it('hides the export button without the payable.export permission', () => {
    canExportPayable = false
    build()

    expect(screen.queryByRole('button', { name: /Xuất Excel/ })).not.toBeInTheDocument()
    // Nút tạo đề nghị thanh toán vẫn còn — hai quyền độc lập nhau.
    expect(submitButton()).toBeInTheDocument()
  })
})

describe('PayableListPage — khoảng ngày', () => {
  function lastCall() {
    return listCalls[listCalls.length - 1]
  }

  it('sends the range as due dates by default — that is the "kỳ chi tiền" question', () => {
    build('/finance/payables?date_from=2026-08-01&date_to=2026-08-31')

    expect(lastCall()).toMatchObject({ due_from: '2026-08-01', due_to: '2026-08-31' })
    expect(lastCall().incur_from).toBeUndefined()
  })

  it('switches to the incur dates when the user picks that mốc', () => {
    build('/finance/payables?date_field=incur&date_from=2026-08-01&date_to=2026-08-31')

    expect(lastCall()).toMatchObject({ incur_from: '2026-08-01', incur_to: '2026-08-31' })
    expect(lastCall().due_from).toBeUndefined()
  })

  it('forces year=all while a range is active, even if the URL still names a year', () => {
    //  Backend mặc định lọc theo NĂM HIỆN TẠI khi không nhận `year`. Khoảng vắt
    //  qua giao thừa mà vẫn kẹp năm thì bảng trả về rỗng, người dùng tưởng kỳ đó
    //  không nợ ai đồng nào.
    build('/finance/payables?year=2026&date_from=2025-12-20&date_to=2026-01-10')

    expect(lastCall().year).toBe('all')
  })

  it('keeps the year filter when there is no range', () => {
    build('/finance/payables?year=2025')

    expect(lastCall().year).toBe('2025')
    expect(lastCall().due_from).toBeUndefined()
    expect(lastCall().due_to).toBeUndefined()
  })

  it('accepts a half-open range — "từ 01/08 tới nay" is a real question', () => {
    build('/finance/payables?date_from=2026-08-01')

    expect(lastCall().due_from).toBe('2026-08-01')
    expect(lastCall().due_to).toBeUndefined()
    expect(lastCall().year).toBe('all')
  })

  it('locks the year select while a range is active', () => {
    build('/finance/payables?date_from=2026-08-01&date_to=2026-08-31')

    //  Khóa suông thì người dùng tưởng hỏng, nên câu giải thích là một phần của
    //  tính năng — tìm ô Năm qua đúng câu đó.
    const yearSelect = screen.getByTitle(/Đang lọc theo khoảng ngày/)
    expect(yearSelect).toBeDisabled()
    expect(yearSelect).toHaveTextContent('Tất cả các năm')
  })
})

/**
 * bao-CR-447 — khoảng TIỀN.
 *
 * Backend đọc `amount_from` / `amount_to` (so trên `Payable.total`) và bản v1 có
 * đủ cặp ô này, nhưng v2 thì không có ở đâu cả: không trên thanh công cụ, cũng
 * không trong bộ lọc điều kiện. Câu "khoản nào trên 100 triệu" không hỏi được.
 */
describe('PayableListPage — khoảng tiền', () => {
  function lastCall() {
    return listCalls[listCalls.length - 1]
  }

  it('sends both ends of the range', () => {
    build('/finance/payables?amount_from=1000000&amount_to=5000000')

    expect(lastCall()).toMatchObject({ amount_from: '1000000', amount_to: '5000000' })
  })

  it('accepts a half-open range — "từ 100 triệu trở lên" is a real question', () => {
    build('/finance/payables?amount_from=100000000')

    expect(lastCall().amount_from).toBe('100000000')
    expect(lastCall().amount_to).toBeUndefined()
  })

  it('sends nothing when both boxes are empty', () => {
    //  Gửi `amount_from=""` xuống là backend ép kiểu số trên chuỗi rỗng — hoặc nổ
    //  500, hoặc hiểu thành 0 và cắt mất khoản nợ âm (hàng trả lại).
    build('/finance/payables?amount_from=&amount_to=')

    expect(lastCall().amount_from).toBeUndefined()
    expect(lastCall().amount_to).toBeUndefined()
  })

  it('keeps a zero bound out of the query — ô vẽ ra TRỐNG thì đừng lọc', () => {
    //  `formatNumberVn(0)` trả chuỗi rỗng nên `amount_from=0` hiện thành một ô
    //  trống trơn. Gửi nó xuống là bảng đang bị cắt mất các khoản ÂM (hàng trả
    //  lại) mà trên màn hình không có dấu hiệu nào.
    build('/finance/payables?amount_from=0&amount_to=0')

    expect(lastCall().amount_from).toBeUndefined()
    expect(lastCall().amount_to).toBeUndefined()
  })

  it('drops a junk bound instead of sending it to the backend', () => {
    //  Sửa tay URL không được làm vỡ trang: `Number('abc')` là `NaN`, và
    //  `amount_from=abc` xuống tới `float()` bên backend là lỗi 500.
    build('/finance/payables?amount_from=abc')

    expect(lastCall().amount_from).toBeUndefined()
  })

  it('keeps a negative lower bound — khoản âm là hàng trả lại, hỏi được', () => {
    build('/finance/payables?amount_from=-500000')

    expect(lastCall().amount_from).toBe('-500000')
  })

  it('exports the SAME amount range the table is showing', async () => {
    const user = userEvent.setup()
    build('/finance/payables?amount_from=1000000&amount_to=5000000')

    await user.click(screen.getByRole('button', { name: /Xuất Excel/ }))

    expect(downloadFileMock.mock.calls[0][2]).toMatchObject({
      amount_from: '1000000',
      amount_to: '5000000',
    })
  })

  it('ai-CR-017: không còn bày cặp ô tiền thẳng trên thanh công cụ — phải mở nút Bộ lọc trước', () => {
    // Đúng yêu cầu AI-0007: khoảng tiền dời vào popover "Bộ lọc", không còn
    // hiện sẵn ngoài thanh công cụ nữa (Radix Popover không mount nội dung khi
    // đang đóng).
    build()

    expect(screen.queryByLabelText('Lọc tổng nợ từ')).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Lọc tổng nợ đến')).not.toBeInTheDocument()
  })

  it('bày cặp ô tiền bên trong popover "Bộ lọc" sau khi mở', async () => {
    const user = userEvent.setup()
    build()

    await user.click(await desktopFilterTrigger())

    expect(screen.getAllByLabelText('Lọc tổng nợ từ').length).toBeGreaterThan(0)
    expect(screen.getAllByLabelText('Lọc tổng nợ đến').length).toBeGreaterThan(0)
  })
})

/** ai-CR-017: đồng bộ v1 — Nhà cung cấp / Số hóa đơn / Loại nợ ra thanh lọc ngoài. */
describe('PayableListPage — ba ô lọc bù từ Bộ lọc điều kiện (ai-CR-017)', () => {
  function lastCall() {
    return listCalls[listCalls.length - 1]
  }

  it('sends supplier_code when a supplier is picked from the outer quick filter', async () => {
    const user = userEvent.setup()
    build()

    await user.click(screen.getByRole('combobox', { name: 'Lọc theo nhà cung cấp' }))
    await user.click(screen.getByRole('option', { name: 'Nhà cung cấp 1 (NCC-1)' }))

    expect(lastCall().supplier_code).toBe('NCC-1')
  })

  it('sends invoice_no only after the debounce settles, and drops it when cleared', async () => {
    const user = userEvent.setup()
    build()

    await user.type(screen.getByLabelText('Lọc theo số hóa đơn'), 'HD-9')
    expect(lastCall().invoice_no).toBeUndefined()

    await vi.waitFor(() => expect(lastCall().invoice_no).toBe('HD-9'), { timeout: 1000 })

    await user.clear(screen.getByLabelText('Lọc theo số hóa đơn'))
    await vi.waitFor(() => expect(lastCall().invoice_no).toBeUndefined(), { timeout: 1000 })
  })

  it('sends source_type when Loại nợ is picked', async () => {
    const user = userEvent.setup()
    build()

    await user.click(screen.getByRole('combobox', { name: 'Lọc theo loại nợ' }))
    await user.click(screen.getByRole('option', { name: 'Vận chuyển' }))

    expect(lastCall().source_type).toBe('shipping')
  })

})
