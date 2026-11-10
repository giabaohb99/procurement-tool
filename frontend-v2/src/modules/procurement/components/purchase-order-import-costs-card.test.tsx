import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type {
  PurchaseOrderDetail,
  PurchaseOrderImportCost,
} from '../types/purchase-order-detail'
import { createEmptyImportCost } from '../utils/purchase-order-draft'
import { PurchaseOrderImportCostsCard } from './purchase-order-import-costs-card'

// Thẻ này nói về CÁCH HIỆN bảng khoản chi phí, không nói về quyền hay mạng — cắt hai nguồn đó.
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => false }),
}))
vi.mock('../hooks/use-po-cost-types', () => ({
  usePoCostTypes: () => ({ data: { items: [], total: 0 }, isLoading: false }),
}))

function cost(overrides: Partial<PurchaseOrderImportCost>): PurchaseOrderImportCost {
  return { ...createEmptyImportCost(), ...overrides }
}

// Thứ tự gốc (Gamma, Alpha, Beta) cố ý không xếp sẵn theo cột nào được kiểm.
// `description` làm NHÃN ĐỊNH DANH của khoản.
const COSTS: PurchaseOrderImportCost[] = [
  cost({
    id: 1,
    description: 'Gamma',
    cost_type: 1,
    cost_type_label: 'Cước biển',
    supplier_code: 'S2',
    supplier_name: 'Hãng tàu',
    currency: 'USD',
    vat: 8,
    estimate_amount: 100,
    estimate_rate: 25000,
    estimate_base: 2_700_000,
    provisional_amount: 120,
    provisional_rate: 25000,
    provisional_base: 3_240_000,
    allocation_method_label: 'Theo giá trị',
    invoice_no: 'HD-10',
    invoice_date: '2026-03-10',
    base_amount: 2_700_000,
  }),
  cost({
    id: 2,
    description: 'Alpha',
    cost_type: 2,
    cost_type_label: 'Bảo hiểm',
    // Chưa chọn NCC -> ô trống, phải xuống cuối ở cả hai chiều.
    supplier_code: '',
    supplier_name: '',
    currency: 'VND',
    vat: 0,
    estimate_amount: 900,
    estimate_rate: 1,
    estimate_base: 900,
    allocation_method_label: 'Chia đều',
    invoice_no: 'HD-9',
    invoice_date: '2026-01-15',
    base_amount: 900,
  }),
  cost({
    id: 3,
    description: 'Beta',
    cost_type: 3,
    cost_type_label: 'Phí cảng',
    supplier_code: 'S1',
    supplier_name: 'Khai thuê',
    currency: 'EUR',
    vat: 10,
    estimate_amount: 10,
    estimate_rate: 30000,
    estimate_base: 330_000,
    allocation_method_label: 'Theo trọng lượng',
    invoice_no: '',
    invoice_date: '',
    base_amount: 330_000,
  }),
]

const ORDER = {
  id: 7,
  status: 'draft',
  order_type: 2,
  currency: 'USD',
  exchange_rate: 25000,
  cost_stage: 1,
  items: [],
  import_costs: COSTS,
} as unknown as PurchaseOrderDetail

function renderCard(costs = COSTS) {
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter>
        <PurchaseOrderImportCostsCard
          order={{ ...ORDER, import_costs: costs }}
          editable={false}
          isNew={false}
          suppliers={[]}
          onChange={vi.fn()}
        />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

/** Bảng khoản chi phí — thẻ còn nhiều bảng khác (gom theo loại, theo NCC) cũng có hàng. */
function costTable(): HTMLElement {
  const table = screen.getByRole('columnheader', { name: /^Diễn giải/ }).closest('table')
  if (!table) throw new Error('không thấy bảng khoản chi phí')
  return table
}

async function clickHeader(name: RegExp) {
  const header = within(costTable()).getByRole('columnheader', { name })
  const clickArea = header.firstElementChild
  if (!clickArea) throw new Error('tiêu đề cột không có vùng bấm')
  await userEvent.click(clickArea)
}

/** Chữ trong cột `name` theo thứ tự dòng đang hiện (bỏ hàng tiêu đề). */
function columnTexts(name: RegExp): string[] {
  const table = within(costTable())
  const index = table.getAllByRole('columnheader').findIndex((h) => name.test(h.textContent ?? ''))
  return table
    .getAllByRole('row')
    .slice(1)
    .map((row) => within(row).getAllByRole('cell')[index]?.textContent ?? '')
}

const order = () => columnTexts(/^Diễn giải/)

/**
 * duoc-CR-744 — bấm tiêu đề cột xếp khoản chi phí theo đúng thứ ô ĐANG HIỆN: loại chi phí
 * và cách phân bổ theo NHÃN, NCC theo chuỗi "mã — tên", ba cột giai đoạn theo số quy đổi
 * VNĐ (không theo số nguyên tệ), ô trống luôn xuống cuối ở cả hai chiều.
 */
describe('PurchaseOrderImportCostsCard — xếp cột bảng khoản chi phí (duoc-CR-744)', () => {
  beforeEach(() => localStorage.clear())
  afterEach(() => localStorage.clear())

  it('sorts by the description asc, then desc, then back to the original order', async () => {
    renderCard()
    expect(order()).toEqual(['Gamma', 'Alpha', 'Beta'])

    await clickHeader(/^Diễn giải/)
    expect(order()).toEqual(['Alpha', 'Beta', 'Gamma'])
    await clickHeader(/^Diễn giải/)
    expect(order()).toEqual(['Gamma', 'Beta', 'Alpha'])
    await clickHeader(/^Diễn giải/)
    expect(order()).toEqual(['Gamma', 'Alpha', 'Beta'])
  })

  it('sorts Loại chi phí by the displayed label, not by the numeric cost_type', async () => {
    renderCard()
    //  Nhãn: Bảo hiểm (Alpha) < Cước biển (Gamma) < Phí cảng (Beta); theo cost_type số sẽ là Gamma, Alpha, Beta.
    await clickHeader(/^Loại chi phí/)
    expect(order()).toEqual(['Alpha', 'Gamma', 'Beta'])
  })

  it('sorts the supplier and keeps the line without a supplier last in both directions', async () => {
    renderCard()
    //  "S1 — Khai thuê" (Beta) < "S2 — Hãng tàu" (Gamma); Alpha chưa chọn NCC.
    await clickHeader(/^Nhà cung cấp/)
    expect(order()).toEqual(['Beta', 'Gamma', 'Alpha'])
    await clickHeader(/^Nhà cung cấp/)
    expect(order()).toEqual(['Gamma', 'Beta', 'Alpha'])
  })

  it('sorts Dự toán by the VND conversion, not by the foreign-currency amount', async () => {
    renderCard()
    //  Nguyên tệ: Gamma 100 USD · Alpha 900 VND · Beta 10 EUR. Quy đổi VNĐ: 2.700.000 · 900 · 330.000.
    await clickHeader(/^Dự toán/)
    expect(order()).toEqual(['Alpha', 'Beta', 'Gamma'])
    await clickHeader(/^Dự toán/)
    expect(order()).toEqual(['Gamma', 'Beta', 'Alpha'])
  })

  it('leaves a stage nobody has filled blank and sorts it last, ascending and descending', async () => {
    renderCard()
    //  Chỉ Gamma có Tạm tính.
    await clickHeader(/^Tạm tính/)
    expect(order()).toEqual(['Gamma', 'Alpha', 'Beta'])
    await clickHeader(/^Tạm tính/)
    expect(order()).toEqual(['Gamma', 'Alpha', 'Beta'])
  })

  it('sorts Quy đổi (VNĐ) by number and Cách phân bổ by label', async () => {
    renderCard()
    await clickHeader(/^Quy đổi/)
    expect(order()).toEqual(['Alpha', 'Beta', 'Gamma'])
    await clickHeader(/^Cách phân bổ/)
    //  Chia đều (Alpha) < Theo giá trị (Gamma) < Theo trọng lượng (Beta)
    expect(order()).toEqual(['Alpha', 'Gamma', 'Beta'])
  })

  it('sorts the currency and VAT columns, and treats the invoice number with digits naturally', async () => {
    renderCard()
    await clickHeader(/^VAT/)
    expect(order()).toEqual(['Alpha', 'Gamma', 'Beta'])
    await clickHeader(/^Tiền tệ/)
    //  EUR (Beta) < USD (Gamma) < VND (Alpha)
    expect(order()).toEqual(['Beta', 'Gamma', 'Alpha'])
    await clickHeader(/^Số hóa đơn/)
    //  HD-9 < HD-10 (hiểu số trong chữ), khoản không có hóa đơn xuống cuối.
    expect(order()).toEqual(['Alpha', 'Gamma', 'Beta'])
  })

  it('sorts the invoice date by the ISO value once the full table shows the date columns', async () => {
    renderCard()
    //  Bảng mở ở dạng rút gọn: cột Ngày hóa đơn nằm trong nhóm cột phụ.
    await userEvent.click(screen.getByRole('button', { name: 'Bảng đầy đủ' }))
    //  10/03/2026 (Gamma) · 15/01/2026 (Alpha) · trống (Beta): so chữ dd/mm sẽ đặt Gamma trước Alpha.
    await clickHeader(/^Ngày hóa đơn/)
    expect(order()).toEqual(['Alpha', 'Gamma', 'Beta'])
    await clickHeader(/^Ngày hóa đơn/)
    expect(order()).toEqual(['Gamma', 'Alpha', 'Beta'])
  })

  it('does not make the # and Hành động headers clickable', async () => {
    renderCard()
    await clickHeader(/^Diễn giải/)
    await clickHeader(/^Diễn giải/)
    expect(order()).toEqual(['Gamma', 'Beta', 'Alpha'])

    await clickHeader(/^#/)
    await clickHeader(/^Hành động/)
    expect(order()).toEqual(['Gamma', 'Beta', 'Alpha'])
  })

  it('does not crash when the order has no cost lines', () => {
    renderCard([])
    expect(screen.getByText('Chưa khai chi phí nào cho lô hàng này')).toBeInTheDocument()
  })
})
