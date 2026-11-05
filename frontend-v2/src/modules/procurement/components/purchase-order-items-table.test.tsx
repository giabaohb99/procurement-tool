import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { PRODUCT_LOCK_HINT, type PurchaseOrderItem } from '../types/purchase-order-detail'
import type { LineReportProgress } from '../utils/survey-report-helpers'
import { PurchaseOrderItemsTable } from './purchase-order-items-table'

// Bảng này nói về CÁCH HIỆN dòng hàng, không nói về mạng — cắt lượt gọi danh mục.
vi.mock('../hooks/use-purchase-request-support', () => ({
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

function item(overrides: Partial<PurchaseOrderItem>): PurchaseOrderItem {
  return {
    id: 501,
    product_code: 'ABA36',
    product_name: 'Abamectin 3.6EC',
    invoice_name: '',
    item_group: '',
    spec: '',
    fg_code: '',
    fg_name: '',
    invoice_no: '',
    invoice_date: '',
    document_delivery_date: '',
    supplier_ready: false,
    required_date: '',
    expected_date: '',
    unit: 'Lít',
    qty_request: 0,
    qty_order: 10,
    price: 1000,
    vat: 0,
    warehouse_code: '',
    note: '',
    currency: '',
    exchange_rate: 0,
    weight_kg: 0,
    dimension: '',
    deliveries: [],
    ...overrides,
  }
}

const ITEMS = [item({ id: 501 }), item({ id: 502, product_code: 'DK', product_name: 'Dầu khoáng' })]

function renderTable(props: Partial<Parameters<typeof PurchaseOrderItemsTable>[0]> = {}) {
  return render(
    <PurchaseOrderItemsTable
      items={ITEMS}
      editable={false}
      progressEditable={false}
      onChange={vi.fn()}
      {...props}
    />,
  )
}

/** bao-CR-602 — cột "Hồ sơ": % báo cáo thực hiện theo dòng, bấm là cuộn tới khối báo cáo. */
describe('PurchaseOrderItemsTable — cột Hồ sơ (báo cáo thực hiện theo dòng)', () => {
  beforeEach(() => localStorage.clear())
  afterEach(() => localStorage.clear())

  it('hides the column entirely when no report map is passed (create screen)', () => {
    renderTable()
    expect(screen.queryByText('Hồ sơ')).toBeNull()
  })

  it('shows the per-line percent and calls back with the report item to focus', async () => {
    const onOpenLineReport = vi.fn()
    const lineReport = new Map<number, LineReportProgress>([
      [501, { itemId: 11, done: 3, total: 4, percent: 75 }],
    ])
    renderTable({ lineReport, onOpenLineReport })

    expect(screen.getByText('Hồ sơ')).toBeInTheDocument()
    const button = screen.getByRole('button', { name: 'Hồ sơ dòng 1: 75%' })
    expect(button).toHaveTextContent('75%')
    await userEvent.click(button)
    expect(onOpenLineReport).toHaveBeenCalledWith({ itemId: 11, done: 3, total: 4, percent: 75 })

    //  Dòng chưa có hồ sơ nào (không có trong map) hiện gạch ngang, không có nút để bấm hụt.
    expect(screen.queryByRole('button', { name: /Hồ sơ dòng 2/ })).toBeNull()
  })

  it('treats a line with zero docs as "no report" rather than 0%', () => {
    const lineReport = new Map<number, LineReportProgress>([
      [501, { itemId: 11, done: 0, total: 0, percent: 0 }],
    ])
    renderTable({ lineReport })
    expect(screen.queryByRole('button', { name: /Hồ sơ dòng 1/ })).toBeNull()
  })
})

/**
 * duoc-CR-720 — khổ điện thoại đổi bảng sang THẺ. `setup.ts` cố định `matchMedia`
 * ở khổ desktop cho cả bộ test, nên khổ hẹp phải nói rõ ngay tại đây.
 */
describe('PurchaseOrderItemsTable — khổ điện thoại', () => {
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

  it('swaps the grid for one card per line and keeps the line count', () => {
    const { container } = renderTable()
    expect(container.querySelector('table')).toBeNull()
    expect(screen.getByText('2 dòng')).toBeInTheDocument()
    expect(screen.getByText('Abamectin 3.6EC')).toBeInTheDocument()
    expect(screen.getByText('Dầu khoáng')).toBeInTheDocument()
  })

  it('opens the line detail dialog by index when a card is tapped', async () => {
    const onOpenDetail = vi.fn()
    renderTable({ onOpenDetail })
    await userEvent.click(screen.getByRole('button', { name: /Chi tiết dòng 2/ }))
    expect(onOpenDetail).toHaveBeenCalledWith(1)
  })

  it('duplicates and removes lines from the card exactly like the table does', async () => {
    const onChange = vi.fn()
    const onLineRemoved = vi.fn()
    const onLineDuplicated = vi.fn()
    renderTable({ editable: true, onChange, onLineRemoved, onLineDuplicated })

    await userEvent.click(screen.getAllByRole('button', { name: 'Nhân bản dòng' })[0])
    const duplicated = onChange.mock.calls[0][0] as PurchaseOrderItem[]
    expect(duplicated).toHaveLength(3)
    // Bản sao là dòng MỚI: không mang id, không mang các lần giao của dòng gốc.
    expect(duplicated[1].id).toBeUndefined()
    expect(duplicated[1].deliveries).toEqual([])
    expect(onLineDuplicated).toHaveBeenCalledWith(0)

    await userEvent.click(screen.getAllByRole('button', { name: 'Xóa dòng' })[1])
    expect(onChange.mock.calls[1][0]).toHaveLength(1)
    expect(onLineRemoved).toHaveBeenCalledWith(1)
  })

  /**
   * Lỗi chặn rà ra ở duoc-CR-720: hộp Chi tiết dòng KHÔNG có mã hàng / SL đặt / đơn
   * giá / VAT (bảng chỉ sửa chúng tại ô), nên thẻ thiếu các ô đó thì dòng mới thêm
   * trên điện thoại kẹt ở "(chưa chọn hàng)" — không chọn được hàng, không nhập giá.
   */
  it('lets a new line pick a product and type qty, price and VAT right on the card', async () => {
    const onChange = vi.fn()
    renderTable({
      editable: true,
      onChange,
      items: [item({ id: undefined, product_code: '', product_name: '', qty_order: 0, price: 0 })],
    })

    expect(within(screen.getByRole('group', { name: 'Mã hàng' })).getByRole('button')).toBeInTheDocument()
    expect(screen.getByRole('group', { name: 'VAT%' })).toBeInTheDocument()

    await userEvent.type(within(screen.getByRole('group', { name: 'SL đặt' })).getByRole('textbox'), '5')
    expect(onChange).toHaveBeenLastCalledWith([expect.objectContaining({ qty_order: 5 })])

    await userEvent.type(within(screen.getByRole('group', { name: 'Đơn giá' })).getByRole('textbox'), '7')
    expect(onChange).toHaveBeenLastCalledWith([expect.objectContaining({ price: 7 })])
  })

  it('locks the product on a received line like the table, but keeps qty and price editable', () => {
    renderTable({ editable: true, items: [item({ qty_received: 3 })] })

    const code = screen.getByRole('group', { name: 'Mã hàng' })
    // Đã nhận hàng: kho đã ghi theo mã cũ, ô mã hàng thành chữ chỉ đọc.
    expect(within(code).getByText('ABA36')).toHaveAttribute('title', PRODUCT_LOCK_HINT)
    expect(within(screen.getByRole('group', { name: 'SL đặt' })).getByRole('textbox')).toBeInTheDocument()
  })

  it('shows no inline editor on a read-only order or a completed line', () => {
    const { unmount } = renderTable({ editable: false })
    expect(screen.queryByRole('group', { name: 'SL đặt' })).toBeNull()
    unmount()

    renderTable({ editable: true, items: [item({ progress_status: 'completed' })] })
    expect(screen.queryByRole('group', { name: 'SL đặt' })).toBeNull()
  })

  it('drops the VAT field on import orders, as the table drops the column', () => {
    renderTable({
      editable: true,
      order: { order_type: 2, currency: 'USD', exchange_rate: 25_000 },
    })
    expect(screen.getAllByRole('group', { name: 'Đơn giá' }).length).toBeGreaterThan(0)
    expect(screen.queryByRole('group', { name: 'VAT%' })).toBeNull()
  })

  it('keeps bulk delete reachable: select-all ticks every unlocked line', async () => {
    renderTable({
      editable: true,
      bulkRemovable: true,
      items: [ITEMS[0], item({ id: 502, product_name: 'Dầu khoáng', progress_status: 'completed' })],
    })

    expect(screen.getByRole('checkbox', { name: 'Chọn dòng 2' })).toBeDisabled()
    await userEvent.click(screen.getByRole('checkbox', { name: 'Chọn tất cả' }))
    expect(screen.getByRole('checkbox', { name: 'Chọn dòng 1' })).toBeChecked()
    expect(screen.getByRole('button', { name: 'Xóa đã chọn (1)' })).toBeInTheDocument()
  })
})
