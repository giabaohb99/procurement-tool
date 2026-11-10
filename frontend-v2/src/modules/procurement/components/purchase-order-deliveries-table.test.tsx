import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { PurchaseOrderDelivery, PurchaseOrderItem } from '../types/purchase-order-detail'
import { PurchaseOrderDeliveriesTable } from './purchase-order-deliveries-table'

// Bảng này nói về CÁCH HIỆN các lần giao, không nói về mạng — cắt lượt gọi danh mục kho
// và tệp đính kèm của từng lần giao.
vi.mock('../hooks/use-purchase-request-support', () => ({
  usePurchaseRequestWarehouses: () => ({ data: { items: [] }, isLoading: false }),
  usePurchaseRequestAttachments: () => ({ data: [], isLoading: false }),
  useUploadPurchaseRequestAttachments: () => ({ mutate: vi.fn(), isPending: false }),
  useDeletePurchaseRequestAttachment: () => ({ mutate: vi.fn(), isPending: false }),
}))

function delivery(overrides: Partial<PurchaseOrderDelivery>): PurchaseOrderDelivery {
  return {
    delivery_no: 1,
    warehouse_code: '',
    carrier_code: '',
    carrier_name: '',
    ship_qty: 0,
    ship_unit: '',
    received_qty: 0,
    promised_date: '',
    expected_date: '',
    received_date: '',
    std_days: 0,
    invoice_no: '',
    invoice_date: '',
    shipping_unit_price: 0,
    shipping_amount: 0,
    qc_result: '',
    extra_request: '',
    progress_note: '',
    ...overrides,
  }
}

// Dòng hàng: 100 đ, VAT 10% -> thành tiền nhận = SL nhận x 110.
// `extra_request` làm NHÃN ĐỊNH DANH của lần giao (không cột nào được kiểm xếp theo nó).
const DELIVERIES: PurchaseOrderDelivery[] = [
  delivery({
    id: 1,
    extra_request: 'X',
    delivery_no: 2,
    warehouse_code: 'KHO-B',
    carrier_name: 'Viettel',
    received_qty: 10,
    shipping_amount: 500,
    status: 'received',
    invoice_date: '2026-03-10',
    paid: 100,
    remaining: 50,
    received_date: '2026-03-05',
    diff_promise: -2,
  }),
  delivery({
    id: 2,
    extra_request: 'Y',
    delivery_no: 3,
    warehouse_code: 'KHO-C',
    carrier_name: 'Aramex',
    received_qty: 2,
    shipping_amount: 900,
    status: 'pending',
    invoice_date: '2026-01-15',
    paid: 0,
    remaining: 30,
    // Chưa nhận hàng: ô "Trễ CK" để trống dù backend có trả số.
    received_date: '',
    diff_promise: 5,
  }),
  // Lần giao chưa lưu (không có id): công nợ để trống.
  delivery({
    extra_request: 'Z',
    delivery_no: 1,
    warehouse_code: 'KHO-A',
    carrier_name: '',
    received_qty: 5,
    shipping_amount: 0,
    status: 'defect',
    invoice_date: '',
    received_date: '2026-03-20',
    diff_promise: 4,
  }),
]

function renderTable(deliveries = DELIVERIES) {
  const item = {
    qty_order: 20,
    price: 100,
    vat: 10,
    required_date: '2026-03-01',
    deliveries,
  } as PurchaseOrderItem
  return render(
    <PurchaseOrderDeliveriesTable
      item={item}
      editable={false}
      carriers={[]}
      attachEditable={false}
      purchaseOrderId={9}
      pendingFiles={{}}
      onChange={vi.fn()}
      onPendingFilesChange={vi.fn()}
    />,
  )
}

async function clickHeader(name: RegExp) {
  const header = screen.getByRole('columnheader', { name })
  const clickArea = header.firstElementChild
  if (!clickArea) throw new Error('tiêu đề cột không có vùng bấm')
  await userEvent.click(clickArea)
}

/** Chữ trong cột `name` theo thứ tự dòng đang hiện (bỏ hàng tiêu đề). */
function columnTexts(name: RegExp): string[] {
  const index = screen.getAllByRole('columnheader').findIndex((h) => name.test(h.textContent ?? ''))
  return screen
    .getAllByRole('row')
    .slice(1)
    .map((row) => within(row).getAllByRole('cell')[index]?.textContent ?? '')
}

const order = () => columnTexts(/^Yêu cầu khác/)

/**
 * duoc-CR-744 — bấm tiêu đề cột xếp các lần giao theo đúng thứ ô ĐANG HIỆN: thành tiền
 * nhận là số tính từ dòng hàng, trạng thái xếp theo dòng đời, ô công nợ / mốc trễ để trống
 * ở những lần giao chưa lưu hoặc chưa nhận hàng thì phải xuống cuối cả hai chiều.
 */
describe('PurchaseOrderDeliveriesTable — xếp cột khi bấm tiêu đề (duoc-CR-744)', () => {
  beforeEach(() => localStorage.clear())
  afterEach(() => localStorage.clear())

  it('sorts by the delivery number asc, then desc, then back to the original order', async () => {
    renderTable()
    expect(order()).toEqual(['X', 'Y', 'Z'])

    await clickHeader(/^Lần/)
    expect(order()).toEqual(['Z', 'X', 'Y'])
    await clickHeader(/^Lần/)
    expect(order()).toEqual(['Y', 'X', 'Z'])
    await clickHeader(/^Lần/)
    expect(order()).toEqual(['X', 'Y', 'Z'])
  })

  it('sorts the carrier by the displayed name and keeps the blank one last in both directions', async () => {
    renderTable()
    await clickHeader(/^Đơn vị vận chuyển/)
    expect(order()).toEqual(['Y', 'X', 'Z'])
    await clickHeader(/^Đơn vị vận chuyển/)
    expect(order()).toEqual(['X', 'Y', 'Z'])
  })

  it('sorts Thành tiền (nhận) by the computed received qty x price x (1 + VAT)', async () => {
    renderTable()
    //  X 10x110=1.100 · Y 2x110=220 · Z 5x110=550
    await clickHeader(/^Thành tiền \(nhận\)/)
    expect(order()).toEqual(['Y', 'Z', 'X'])
    await clickHeader(/^Thành tiền \(nhận\)/)
    expect(order()).toEqual(['X', 'Z', 'Y'])
  })

  it('sorts Trạng thái giao along the delivery life cycle, not by the English code', async () => {
    renderTable()
    //  Dòng đời: pending < received < defect. Theo mã chữ cái sẽ là defect < pending < received.
    await clickHeader(/^Trạng thái giao/)
    expect(order()).toEqual(['Y', 'X', 'Z'])
  })

  it('sorts dates by the ISO value, not by the dd/mm/yyyy text shown in the cell', async () => {
    renderTable()
    //  X hiện 10/03/2026, Y hiện 15/01/2026: so chữ dd/mm sẽ ra X trước Y, so ISO ra Y trước X.
    await clickHeader(/^Ngày hóa đơn/)
    expect(order()).toEqual(['Y', 'X', 'Z'])
    await clickHeader(/^Ngày hóa đơn/)
    expect(order()).toEqual(['X', 'Y', 'Z'])
  })

  it('leaves the debt columns blank for an unsaved delivery and sorts it last, zero included', async () => {
    renderTable()
    await clickHeader(/^Đã trả/)
    expect(order()).toEqual(['Y', 'X', 'Z'])
    await clickHeader(/^Đã trả/)
    expect(order()).toEqual(['X', 'Y', 'Z'])
  })

  it('treats the lateness cells as blank until goods are received', async () => {
    renderTable()
    //  Y có diff_promise = 5 nhưng chưa nhận hàng -> ô trống -> luôn cuối.
    await clickHeader(/^Trễ CK/)
    expect(order()).toEqual(['X', 'Z', 'Y'])
    await clickHeader(/^Trễ CK/)
    expect(order()).toEqual(['Z', 'X', 'Y'])
  })

  it('does not make the file and action headers clickable', async () => {
    renderTable()
    await clickHeader(/^Lần/)
    expect(order()).toEqual(['Z', 'X', 'Y'])

    await clickHeader(/^Phiếu giao/)
    await clickHeader(/^Thao tác/)
    expect(order()).toEqual(['Z', 'X', 'Y'])
  })

  it('does not crash on an empty list or a single delivery', async () => {
    const { unmount } = renderTable([])
    await clickHeader(/^Lần/)
    expect(screen.getByText('Chưa có lần giao nào.')).toBeInTheDocument()
    unmount()

    renderTable([DELIVERIES[0]])
    await clickHeader(/^Lần/)
    expect(order()).toEqual(['X'])
  })
})
