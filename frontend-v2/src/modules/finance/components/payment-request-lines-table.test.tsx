import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  PaymentRequestLinesTable,
  type EditablePaymentLine,
} from './payment-request-lines-table'

function line(overrides: Partial<EditablePaymentLine>): EditablePaymentLine {
  return {
    key: 'k',
    payable_id: 1,
    supplier_code: '',
    supplier_name: '',
    source_type: 'po',
    po_code: '',
    misa_code: '',
    invoice_no: '',
    invoice_date: '',
    due_date: '',
    payable_total: 0,
    payable_paid: 0,
    amount: 0,
    offset_amount: 0,
    ...overrides,
  }
}

// Thứ tự gốc (Zeta, Alpha, Mid) cố ý không xếp sẵn theo cột nào được kiểm.
const ROWS: EditablePaymentLine[] = [
  line({
    key: 'a',
    supplier_code: 'S2',
    supplier_name: 'Zeta Co',
    source_type: 'po',
    po_code: 'PO-10',
    misa_code: 'M-2',
    invoice_no: 'INV-9',
    invoice_date: '2026-03-10',
    due_date: '2026-04-01',
    payable_total: 25,
    payable_paid: 1000,
    offset_amount: 0,
    amount: 300,
  }),
  line({
    key: 'b',
    supplier_code: 'S1',
    supplier_name: 'Alpha Co',
    source_type: 'import_cost',
    po_code: 'PO-2',
    misa_code: '',
    // Ô hiện "chưa có HĐ" thay vì số -> coi là trống, xuống cuối.
    invoice_no: '',
    invoice_date: '2026-01-15',
    due_date: '2026-02-01',
    payable_total: 9,
    payable_paid: 0,
    offset_amount: 70,
    amount: 1500,
  }),
  line({
    key: 'c',
    supplier_code: 'S3',
    supplier_name: 'Mid Co',
    source_type: 'po',
    po_code: 'PO-1',
    misa_code: 'M-1',
    invoice_no: 'INV-10',
    invoice_date: '',
    due_date: '',
    payable_total: 100,
    payable_paid: 5,
    offset_amount: 10,
    amount: 20,
  }),
]

//  Nhãn Loại nợ cố ý xếp NGƯỢC thứ tự mã (import_cost < po, nhưng "Hàng hóa" < "Phí nhập khẩu").
const SOURCE_LABELS: Record<string, string> = { po: 'Hàng hóa', import_cost: 'Phí nhập khẩu' }

function renderTable(overrides: Partial<Parameters<typeof PaymentRequestLinesTable>[0]> = {}) {
  return render(
    <PaymentRequestLinesTable
      rows={ROWS}
      editable={false}
      storageKey="payment-request-lines-test"
      showSupplierColumns
      lockLinkedPo
      showOffsetColumn
      supplierDisplay={(row) => row.supplier_name}
      sourceDisplay={(row) => SOURCE_LABELS[row.source_type] ?? row.source_type}
      onPatch={vi.fn()}
      onRemove={vi.fn()}
      {...overrides}
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

const order = () => columnTexts(/^Nhà cung cấp/)

/**
 * duoc-CR-744 — bấm tiêu đề cột xếp dòng YCTT theo đúng thứ ô ĐANG HIỆN: NCC và Loại nợ
 * xếp theo CHỮ hiển thị (do trang truyền vào), tiền theo số, ngày theo ISO, ô trống luôn
 * xuống cuối ở cả hai chiều.
 */
describe('PaymentRequestLinesTable — xếp cột khi bấm tiêu đề (duoc-CR-744)', () => {
  beforeEach(() => localStorage.clear())
  afterEach(() => localStorage.clear())

  it('sorts by the displayed supplier name asc, then desc, then back to the original order', async () => {
    renderTable()
    expect(order()).toEqual(['Zeta Co', 'Alpha Co', 'Mid Co'])

    await clickHeader(/^Nhà cung cấp/)
    expect(order()).toEqual(['Alpha Co', 'Mid Co', 'Zeta Co'])
    await clickHeader(/^Nhà cung cấp/)
    expect(order()).toEqual(['Zeta Co', 'Mid Co', 'Alpha Co'])
    await clickHeader(/^Nhà cung cấp/)
    expect(order()).toEqual(['Zeta Co', 'Alpha Co', 'Mid Co'])
  })

  it('sorts Loại nợ by the displayed label, not by the stored code', async () => {
    renderTable()
    //  Theo mã: import_cost (Alpha) < po (Zeta, Mid). Theo nhãn: "Hàng hóa" (Zeta, Mid) < "Phí nhập khẩu" (Alpha).
    await clickHeader(/^Loại nợ/)
    expect(order()).toEqual(['Zeta Co', 'Mid Co', 'Alpha Co'])
  })

  it('sorts Tổng nợ by number (9 < 25 < 100), not by text', async () => {
    renderTable()
    await clickHeader(/^Tổng nợ/)
    expect(order()).toEqual(['Alpha Co', 'Zeta Co', 'Mid Co'])
    await clickHeader(/^Tổng nợ/)
    expect(order()).toEqual(['Mid Co', 'Zeta Co', 'Alpha Co'])
  })

  it('sorts the money columns Đã trả, Cấn trừ trả trước and Đề nghị trả', async () => {
    renderTable()
    await clickHeader(/^Đã trả/)
    expect(order()).toEqual(['Alpha Co', 'Mid Co', 'Zeta Co'])
    await clickHeader(/^Cấn trừ trả trước/)
    expect(order()).toEqual(['Zeta Co', 'Mid Co', 'Alpha Co'])
    await clickHeader(/^Đề nghị trả/)
    expect(order()).toEqual(['Mid Co', 'Zeta Co', 'Alpha Co'])
  })

  it('sorts dates by the ISO value and keeps blank dates last in both directions', async () => {
    renderTable()
    //  Ngày hóa đơn: 10/03/2026 · 15/01/2026 · (trống). So chữ dd/mm sẽ đặt 10/03 trước 15/01.
    await clickHeader(/^Ngày hóa đơn/)
    expect(order()).toEqual(['Alpha Co', 'Zeta Co', 'Mid Co'])
    await clickHeader(/^Ngày hóa đơn/)
    expect(order()).toEqual(['Zeta Co', 'Alpha Co', 'Mid Co'])

    await clickHeader(/^Hạn trả/)
    expect(order()).toEqual(['Alpha Co', 'Zeta Co', 'Mid Co'])
  })

  it('treats a missing invoice number and MISA code as blank and sorts them last', async () => {
    renderTable()
    //  Hiểu số trong chữ: INV-9 < INV-10.
    await clickHeader(/^Số hóa đơn/)
    expect(order()).toEqual(['Zeta Co', 'Mid Co', 'Alpha Co'])
    await clickHeader(/^Số hóa đơn/)
    expect(order()).toEqual(['Mid Co', 'Zeta Co', 'Alpha Co'])

    await clickHeader(/^Mã MISA/)
    expect(order()).toEqual(['Mid Co', 'Zeta Co', 'Alpha Co'])
  })

  it('sorts the PO column by its code text', async () => {
    renderTable()
    await clickHeader(/^PO/)
    //  Hiểu số trong chữ: PO-1 < PO-2 < PO-10.
    expect(order()).toEqual(['Mid Co', 'Alpha Co', 'Zeta Co'])
  })

  it('does not make the # and Bỏ headers clickable', async () => {
    renderTable({ editable: true })
    await clickHeader(/^Nhà cung cấp/)
    await clickHeader(/^Nhà cung cấp/)
    expect(order()).toEqual(['Zeta Co', 'Mid Co', 'Alpha Co'])

    await clickHeader(/^#/)
    await clickHeader(/^Bỏ/)
    expect(order()).toEqual(['Zeta Co', 'Mid Co', 'Alpha Co'])
  })

  it('does not crash on an empty list', async () => {
    renderTable({ rows: [] })
    await clickHeader(/^Nhà cung cấp/)
    expect(screen.getByText('Chưa có dòng nào.')).toBeInTheDocument()
  })
})
