import { render, screen, within } from '@testing-library/react'
import { useState } from 'react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { PurchaseRequestItem } from '../types/purchase-request-detail'
import { PurchaseRequestItemsTable } from './purchase-request-items-table'

// Bảng này nói về CÁCH HIỆN dòng hàng, không nói về mạng — cắt hết lượt gọi
// danh mục (kho / ĐVT / phân loại / sản phẩm / lịch sử mua hàng).
vi.mock('../hooks/use-purchase-request-support', () => ({
  usePurchaseRequestWarehouses: () => ({ data: { items: [] }, isLoading: false }),
  usePurchaseRequestUnits: () => ({ data: { items: [] }, isLoading: false }),
  usePurchaseRequestItemGroups: () => ({ data: { items: [] }, isLoading: false }),
  usePurchaseRequestProducts: () => ({ data: { items: [] }, isLoading: false }),
  useProductPurchaseHistory: () => ({
    data: { total: 0, items: [] },
    isLoading: false,
    isError: false,
    isFetching: false,
  }),
}))

const ITEMS: PurchaseRequestItem[] = [
  {
    id: 7,
    product_code: 'NAP0029',
    product_name: 'Nắp nhựa phi 28',
    item_group: 'Bao bì',
    group_desc: '',
    qty: 1000,
    unit: 'Cái',
    price: 900,
    vat_pct: 8,
    amount: 972000,
    warehouse: 'Kho HCM',
    required_date: '2026-05-20',
    assignee: '',
    expected_date: '',
    line_status: 'no_po',
    progress_note: '',
    note: '',
    qty_ordered: 0,
    qty_received: 0,
    product_id: 3,
    product_thumbnail_url: '',
  },
]

function renderTable(
  props: Partial<Parameters<typeof PurchaseRequestItemsTable>[0]> = {},
) {
  return render(
    <PurchaseRequestItemsTable
      items={ITEMS}
      editing={false}
      onChange={vi.fn()}
      onOpenDetail={vi.fn()}
      {...props}
    />,
  )
}

describe('PurchaseRequestItemsTable', () => {
  beforeEach(() => localStorage.clear())
  afterEach(() => localStorage.clear())

  /**
   * QA 29/08: nút "Sửa dòng hàng" đã BỎ — phiếu còn sửa được thì trang mở thẳng
   * chế độ sửa như v1, bảng chỉ còn hai trạng thái xem / nhập trực tiếp.
   */
  it('không còn nút Sửa dòng hàng — bảng xem là xem, nhập là nhập', () => {
    const { unmount } = renderTable({ editing: false })
    expect(screen.queryByRole('button', { name: /Sửa dòng hàng/ })).toBeNull()
    unmount()

    renderTable({ editing: true })
    expect(screen.getByRole('button', { name: 'Thêm nhiều dòng' })).toBeInTheDocument()
  })

  /**
   * duoc-CR-737: bảng từng có nút *Thêm dòng* trên thanh tiêu đề, làm ĐÚNG việc của
   * *Thêm SP* ở tiêu đề thẻ ngay phía trên — hai nút một lệnh. V1 chỉ có *Thêm SP*.
   */
  it('does not render its own add-one-row button — the card header owns "Thêm SP"', () => {
    renderTable({ editing: true })
    expect(screen.queryByRole('button', { name: /^Thêm dòng$/ })).toBeNull()
  })

  /**
   * Lỗi đã gặp: lúc sửa, mã hàng nằm trong ô CHỌN (một `<button>`) nên bôi đen
   * không được — không ai chép nổi mã đem đi tra ở nơi khác.
   */
  it('mã hàng luôn có nút chép, kể cả khi đang sửa', () => {
    const { unmount } = renderTable({ editing: true })
    expect(screen.getByRole('button', { name: /Chép mã hàng/ })).toBeInTheDocument()
    unmount()

    renderTable({ editing: false })
    expect(screen.getByRole('button', { name: /Chép mã hàng/ })).toBeInTheDocument()
  })
})

/**
 * Khổ điện thoại — bảng đổi sang THẺ, xem `PurchaseRequestLineCard`.
 *
 * Khách báo 14/09/2026: bảng 15–16 cột rộng ~2000px nằm trong khung 322px, phần
 * nhìn thấy được là *No. · Mã hàng* và một mẩu tên hàng — số lượng, thành tiền và
 * trạng thái dòng đều ngoài mép phải, mà thanh cuộn ngang thì iOS ẩn sẵn. Người
 * dùng đọc ra là "chữ bị lỗi" chứ không phải "vuốt sang đi".
 *
 * `setup.ts` cố định `matchMedia` ở khổ desktop cho cả bộ test, nên khổ hẹp phải
 * nói rõ ra ngay tại đây.
 */
describe('PurchaseRequestItemsTable — khổ điện thoại', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.stubGlobal('matchMedia', (query: string) => ({
      matches: true,
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }))
  })
  afterEach(() => {
    vi.unstubAllGlobals()
    localStorage.clear()
  })

  it('bày SỐ LƯỢNG và THÀNH TIỀN của dòng — hai cột nằm ngoài mép phải của bảng', () => {
    renderTable()

    // Số tiền của dòng: `amount` = 972.000 (phiếu đã lưu thì lấy cột backend).
    expect(screen.getByText(/972\.000 đ/)).toBeInTheDocument()
    // SL × đơn giá đứng cùng một mẩu chữ, nên khẳng định theo cả cụm.
    expect(screen.getByText(/1\.000 Cái × 900/)).toBeInTheDocument()
    // Dòng mẫu ở `line_status: 'no_po'` — nhãn tra từ `PR_LINE_STATUS`.
    expect(screen.getByText(/Chưa tạo đơn mua hàng/)).toBeInTheDocument()
  })

  it('KHÔNG bày cụm điều khiển cột — ở chế độ thẻ chúng không điều khiển thứ gì', () => {
    renderTable()

    expect(screen.queryByRole('button', { name: /Cột/ })).toBeNull()
    expect(screen.queryByRole('button', { name: /Bảng rút gọn|Bảng đầy đủ/ })).toBeNull()
  })

  it('the phone card also offers "Nhân đôi" while editing (duoc-CR-741)', async () => {
    const onChange = vi.fn()
    renderTable({ editing: true, onChange })

    const duplicate = screen.getByRole('button', { name: 'Nhân đôi dòng 1' })
    expect(duplicate).toHaveAttribute('title', 'Nhân đôi')
    expect(screen.getByRole('button', { name: 'Xóa dòng 1' })).toHaveAttribute('title', 'Xóa')
    await userEvent.click(duplicate)

    expect((onChange.mock.calls[0][0] as PurchaseRequestItem[]).map((line) => line.id)).toEqual([
      7,
      undefined,
    ])
  })

  it('cả thẻ là một nút mở hộp chi tiết — mọi ô vẫn sửa được ở đó', async () => {
    const onOpenDetail = vi.fn()
    renderTable({ onOpenDetail })

    await userEvent.click(screen.getByRole('button', { name: /Nắp nhựa phi 28/ }))
    expect(onOpenDetail).toHaveBeenCalledWith(0)
  })
})

// bao-CR-547 — tick nhiều dòng rồi "Xóa đã chọn", chỉ khi trang bật `bulkRemovable` (form tạo / Nháp).
describe('PurchaseRequestItemsTable — xóa nhiều dòng (bao-CR-547)', () => {
  const second: PurchaseRequestItem = { ...ITEMS[0], id: 8, product_code: 'NAP0030', product_name: 'Nắp nhựa phi 30' }

  it('shows no checkbox column while editing a rejected-but-editable ticket', () => {
    renderTable({ editing: true, bulkRemovable: false })
    expect(screen.queryByRole('checkbox')).toBeNull()
    expect(screen.queryByRole('button', { name: /Xóa đã chọn/ })).toBeNull()
  })

  it('ticked lines are dropped from the ticket after confirming', async () => {
    const onChange = vi.fn()
    renderTable({ items: [ITEMS[0], second], editing: true, bulkRemovable: true, onChange })

    expect(screen.queryByRole('button', { name: /Xóa đã chọn/ })).toBeNull()
    await userEvent.click(screen.getByRole('checkbox', { name: 'Chọn dòng 1' }))
    await userEvent.click(screen.getByRole('button', { name: 'Xóa đã chọn (1)' }))
    //  duoc-CR-741: hộp hỏi của v1 — câu *Xóa 1 dòng đã chọn?*, nút *Đồng ý* / *Hủy*.
    const dialog = screen.getByRole('alertdialog')
    expect(within(dialog).getByText('Xác nhận')).toBeInTheDocument()
    expect(within(dialog).getByText(/^Xóa 1 dòng đã chọn\? Dòng bỏ khỏi phiếu/)).toBeInTheDocument()
    expect(within(dialog).getByRole('button', { name: 'Hủy' })).toBeInTheDocument()
    await userEvent.click(within(dialog).getByRole('button', { name: 'Đồng ý' }))

    expect(onChange).toHaveBeenCalledWith([second])
  })

  it('select-all then delete empties the ticket in one go', async () => {
    const onChange = vi.fn()
    renderTable({ items: [ITEMS[0], second], editing: true, bulkRemovable: true, onChange })

    await userEvent.click(screen.getByRole('checkbox', { name: 'Chọn tất cả dòng' }))
    await userEvent.click(screen.getByRole('button', { name: 'Xóa đã chọn (2)' }))
    await userEvent.click(screen.getByRole('button', { name: 'Đồng ý' }))

    expect(onChange).toHaveBeenCalledWith([])
  })
})

/**
 * duoc-CR-737 — vị trí nút như bản v1: *Xóa đã chọn (n)* ở góc phải tiêu đề THẺ, *Thêm
 * nhiều* ở DƯỚI bảng. Trang xếp khung qua `renderFrame`; nút lọt lại vào thanh tiêu đề của
 * `LinesTable` là người dời từ v1 sang không tìm thấy.
 */
describe('PurchaseRequestItemsTable — vị trí nút theo v1 (duoc-CR-737)', () => {
  beforeEach(() => localStorage.clear())
  afterEach(() => localStorage.clear())

  const second: PurchaseRequestItem = { ...ITEMS[0], id: 8, product_code: 'NAP0030', product_name: 'Nắp nhựa phi 30' }

  function renderFramed(props: Partial<Parameters<typeof PurchaseRequestItemsTable>[0]> = {}) {
    return renderTable({
      items: [ITEMS[0], second],
      editing: true,
      bulkRemovable: true,
      renderFrame: ({ headerActions, body }) => (
        <>
          <div role="toolbar" aria-label="Tiêu đề thẻ">
            {headerActions}
          </div>
          <div role="region" aria-label="Thân thẻ">
            {body}
          </div>
        </>
      ),
      ...props,
    })
  }

  it('puts "Xóa đã chọn (n)" in the card header slot, not inside the table body', async () => {
    const onChange = vi.fn()
    renderFramed({ onChange })

    const header = screen.getByRole('toolbar', { name: 'Tiêu đề thẻ' })
    const body = screen.getByRole('region', { name: 'Thân thẻ' })
    expect(within(header).queryByRole('button', { name: /Xóa đã chọn/ })).toBeNull()

    await userEvent.click(screen.getByRole('checkbox', { name: 'Chọn dòng 1' }))
    expect(within(header).getByRole('button', { name: 'Xóa đã chọn (1)' })).toBeInTheDocument()
    expect(within(body).queryByRole('button', { name: /Xóa đã chọn/ })).toBeNull()

    await userEvent.click(within(header).getByRole('button', { name: 'Xóa đã chọn (1)' }))
    await userEvent.click(screen.getByRole('button', { name: 'Đồng ý' }))
    expect(onChange).toHaveBeenCalledWith([second])
  })

  it('puts "Thêm nhiều dòng" below the table, after the last row', () => {
    renderFramed()

    const body = screen.getByRole('region', { name: 'Thân thẻ' })
    const addMany = within(body).getByRole('button', { name: 'Thêm nhiều dòng' })
    const table = within(body).getByRole('table')
    // DOCUMENT_POSITION_FOLLOWING: nút đứng SAU bảng trong thứ tự tài liệu.
    expect(table.compareDocumentPosition(addMany) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    expect(within(screen.getByRole('toolbar', { name: 'Tiêu đề thẻ' })).queryByRole('button')).toBeNull()
  })

  it('hides "Thêm nhiều dòng" while only viewing the ticket', () => {
    renderFramed({ editing: false })
    expect(screen.queryByRole('button', { name: /Thêm nhiều/ })).toBeNull()
  })
})

/**
 * duoc-CR-741 — chữ + hành vi theo bản v1: gợi ý nút biểu tượng (*Chi tiết* · *Nhân đôi* ·
 * *Xóa*, lịch sử mua hàng), hộp *Thêm nhiều dòng* hỏi như `askPrompt`, nút *Nhân đôi* dòng.
 */
describe('PurchaseRequestItemsTable — chữ và hành vi v1 (duoc-CR-741)', () => {
  beforeEach(() => localStorage.clear())
  afterEach(() => localStorage.clear())

  const second: PurchaseRequestItem = { ...ITEMS[0], id: 8, product_code: 'NAP0030', product_name: 'Nắp nhựa phi 30' }

  it('row icon tooltips use the v1 words', () => {
    renderTable({ editing: true })

    expect(screen.getByRole('button', { name: 'Chi tiết dòng 1' })).toHaveAttribute('title', 'Chi tiết')
    expect(screen.getByRole('button', { name: 'Nhân đôi dòng 1' })).toHaveAttribute('title', 'Nhân đôi')
    expect(screen.getByRole('button', { name: 'Xóa dòng 1' })).toHaveAttribute('title', 'Xóa')
    expect(screen.getByRole('button', { name: /Xem lịch sử mua hàng của NAP0029/ })).toHaveAttribute(
      'title',
      'Lịch sử mua hàng gần nhất của mã hàng này',
    )
  })

  it('a locked ticket says the history is read-only and offers no duplicate / delete', () => {
    renderTable({ editing: false })

    expect(screen.getByRole('button', { name: /Xem lịch sử mua hàng của NAP0029/ })).toHaveAttribute(
      'title',
      'Lịch sử mua hàng gần nhất của mã hàng này (chỉ xem)',
    )
    expect(screen.queryByRole('button', { name: /Nhân đôi/ })).toBeNull()
    expect(screen.queryByRole('button', { name: /Xóa dòng/ })).toBeNull()
  })

  it('"Nhân đôi" inserts a copy right after the source line, without its id', async () => {
    const onChange = vi.fn()
    renderTable({
      items: [{ ...ITEMS[0], option_count: 2, options_done: true }, second],
      editing: true,
      onChange,
    })

    await userEvent.click(screen.getByRole('button', { name: 'Nhân đôi dòng 1' }))

    const next = onChange.mock.calls[0][0] as PurchaseRequestItem[]
    expect(next.map((line) => line.product_code)).toEqual(['NAP0029', 'NAP0029', 'NAP0030'])
    expect(next[0].id).toBe(7)
    //  Giữ id thì lúc lưu backend ghi đè dòng gốc; giữ phương án thì bản sao trỏ vào phương
    //  án của dòng gốc.
    expect(next[1].id).toBeUndefined()
    expect(next[1].option_count).toBeUndefined()
    expect(next[1].options_done).toBeUndefined()
    expect(next[1].qty).toBe(1000)
    expect(next[2].id).toBe(8)
  })

  it('"Nhân đôi" on the last line appends the copy at the end', async () => {
    const onChange = vi.fn()
    renderTable({ items: [ITEMS[0], second], editing: true, onChange })

    await userEvent.click(screen.getByRole('button', { name: 'Nhân đôi dòng 2' }))

    const next = onChange.mock.calls[0][0] as PurchaseRequestItem[]
    expect(next.map((line) => line.product_code)).toEqual(['NAP0029', 'NAP0030', 'NAP0030'])
  })

  it('"Thêm nhiều dòng" asks like v1 and adds the typed number of empty lines', async () => {
    const onChange = vi.fn()
    renderTable({ editing: true, onChange })

    await userEvent.click(screen.getByRole('button', { name: 'Thêm nhiều dòng' }))
    const dialog = screen.getByRole('dialog', { name: 'Nhập thông tin' })
    expect(within(dialog).getByText('Thêm bao nhiêu dòng?')).toBeInTheDocument()
    expect(within(dialog).getByRole('button', { name: 'Hủy' })).toBeInTheDocument()

    const input = within(dialog).getByRole('spinbutton', { name: 'Số dòng' })
    await userEvent.clear(input)
    await userEvent.type(input, '3')
    await userEvent.click(within(dialog).getByRole('button', { name: 'Xác nhận' }))

    const next = onChange.mock.calls[0][0] as PurchaseRequestItem[]
    expect(next).toHaveLength(4)
    expect(next.slice(1).every((line) => line.product_name === '' && line.id === undefined)).toBe(true)
  })

  it('a typo like 5000 is capped at 50 lines, so it cannot flood the ticket', async () => {
    const onChange = vi.fn()
    renderTable({ editing: true, onChange })

    await userEvent.click(screen.getByRole('button', { name: 'Thêm nhiều dòng' }))
    const input = screen.getByRole('spinbutton', { name: 'Số dòng' })
    await userEvent.clear(input)
    await userEvent.type(input, '5000')
    await userEvent.click(screen.getByRole('button', { name: 'Xác nhận' }))

    expect((onChange.mock.calls[0][0] as PurchaseRequestItem[]).length).toBe(1 + 50)
  })
})

/**
 * Lỗi rà mã duoc-CR-741: dòng chưa lưu khóa tick theo chỉ số (`new-${index}`). Tick dòng 4
 * rồi Nhân đôi dòng 1 thì dòng 3 cũ trôi xuống vị trí 4 và "nhận" dấu tick, nên *Xóa đã
 * chọn (1)* xóa nhầm nó thay vì dòng 4. Nay nhân đôi / xóa một dòng là bỏ hết dấu tick.
 */
describe('PurchaseRequestItemsTable — dấu tick không trôi khi chèn / bỏ dòng', () => {
  const unsaved: PurchaseRequestItem[] = ['A', 'B', 'C', 'D'].map((code) => ({
    ...ITEMS[0],
    id: undefined,
    product_code: code,
    product_name: `Hàng ${code}`,
  }))

  function StatefulTable({ onItems }: { onItems: (items: PurchaseRequestItem[]) => void }) {
    const [items, setItems] = useState(unsaved)
    return (
      <PurchaseRequestItemsTable
        items={items}
        editing
        bulkRemovable
        onChange={(next) => {
          setItems(next)
          onItems(next)
        }}
        onOpenDetail={vi.fn()}
      />
    )
  }

  it('duplicating line 1 clears the tick on line 4, so bulk delete cannot hit the wrong line', async () => {
    const onItems = vi.fn()
    render(<StatefulTable onItems={onItems} />)

    await userEvent.click(screen.getByRole('checkbox', { name: 'Chọn dòng 4' }))
    expect(screen.getByRole('button', { name: 'Xóa đã chọn (1)' })).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Nhân đôi dòng 1' }))

    expect(onItems).toHaveBeenLastCalledWith(
      expect.arrayContaining([expect.objectContaining({ product_code: 'C' })]),
    )
    expect(screen.queryByRole('button', { name: /Xóa đã chọn/ })).toBeNull()
    expect(screen.getByRole('checkbox', { name: 'Chọn dòng 5' })).not.toBeChecked()
    expect(screen.getByRole('checkbox', { name: 'Chọn dòng 4' })).not.toBeChecked()
  })

  it('deleting one line clears the ticks too — the lines after it shift up', async () => {
    const onItems = vi.fn()
    render(<StatefulTable onItems={onItems} />)

    await userEvent.click(screen.getByRole('checkbox', { name: 'Chọn dòng 4' }))
    await userEvent.click(screen.getByRole('button', { name: 'Xóa dòng 1' }))

    const after = onItems.mock.lastCall?.[0] as PurchaseRequestItem[]
    expect(after.map((line) => line.product_code)).toEqual(['B', 'C', 'D'])
    expect(screen.queryByRole('button', { name: /Xóa đã chọn/ })).toBeNull()
  })
})
