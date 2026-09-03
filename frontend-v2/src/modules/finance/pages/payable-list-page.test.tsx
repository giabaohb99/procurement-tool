import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { ListParams } from '@/shared/types/api'
import { PayableListPage } from './payable-list-page'
import type { Payable } from '../types/payable'

//  Chặn ở tầng HOOK dữ liệu chứ không ở `@/core/api`: màn này còn phải bắt được
//  BỘ THAM SỐ nó gửi đi (`due_from` / `incur_from` / `year`), mà tham số đó chỉ
//  hiện nguyên vẹn ở đầu vào của hook.
const listCalls: ListParams[] = []

vi.mock('../hooks/use-payables', () => ({
  usePayables: (params: ListParams) => {
    listCalls.push(params)
    return { data: { total: rows.length, items: rows }, isLoading: false, isError: false }
  },
  usePayableSummary: () => ({
    data: { total: 0, paid: 0, remaining: 0, overdue: 0 },
    isLoading: false,
  }),
  // CR-268: dialog cấn trừ tiền trả trước mount sẵn (đóng) trên trang — thiếu
  // export này là cả trang nổ ngay lúc render, 10 test không liên quan đỏ theo.
  useOffsetPrepay: () => ({ mutateAsync: vi.fn(), isPending: false }),
}))

vi.mock('@/modules/hr/hooks/use-companies', () => ({
  useCompanies: () => ({ data: { total: 1, items: [{ id: 7, name: 'Công ty Dego Cần Thơ' }] } }),
}))

let canCreatePayment = true
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (entity: string) => (entity === 'payment_request' ? canCreatePayment : true),
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

beforeEach(() => {
  listCalls.length = 0
  canCreatePayment = true
  localStorage.clear()
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
