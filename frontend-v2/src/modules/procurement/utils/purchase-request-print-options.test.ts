import { describe, expect, it } from 'vitest'

import type { PurchaseRequestItem } from '../types/purchase-request-detail'
import type { PurchaseRequestOption } from '../types/purchase-request-options'
import {
  PR_OPTION_SOURCE_MANUAL,
  PR_OPTION_SOURCE_ORIGINAL,
} from '../types/purchase-request-options'
import {
  buildSupplierPrintPlan,
  printLineValues,
  printedTotals,
} from './purchase-request-print-options'

function makeOption(overrides: Partial<PurchaseRequestOption> = {}): PurchaseRequestOption {
  return {
    id: 1,
    pr_item_id: 1,
    source: PR_OPTION_SOURCE_MANUAL,
    source_label: 'Nhập tay',
    product_survey_line_id: null,
    public_id: 1,
    display_label: 'Phương án 1',
    is_chosen: true,
    snap_product_name: 'Vải mộc',
    snap_spec: '',
    snap_origin: '',
    snap_quote_unit: '',
    snap_moq: 0,
    snap_price_by_volume: 0,
    snap_volume_range: '',
    snap_vat: 0,
    snap_delivery_time: '',
    snap_delivery_place: '',
    snap_shipping_cost: '',
    snap_sample_ready: '',
    snap_lab_result: '',
    nstm_note: '',
    created_at: '2026-09-15T00:00:00',
    supplier_code: '',
    supplier_name: '',
    supplier_survey_id: 0,
    snap_internal_code: '',
    ...overrides,
  }
}

function makeItem(overrides: Partial<PurchaseRequestItem> = {}): PurchaseRequestItem {
  return {
    id: 1,
    product_code: 'SP-A',
    product_name: 'Vải mộc',
    item_group: 'Nguyên liệu',
    group_desc: '',
    qty: 100,
    unit: 'm',
    price: 4800,
    vat_pct: 8,
    amount: 0,
    warehouse: '',
    required_date: '2026-10-01',
    assignee: 'NV001',
    expected_date: '',
    line_status: 'no_po',
    progress_note: '',
    note: '',
    qty_ordered: 0,
    qty_received: 0,
    product_id: 0,
    product_thumbnail_url: '',
    ...overrides,
  }
}

describe('printLineValues — giá/VAT của dòng theo phương án đã chọn (bản A)', () => {
  it('keeps the proposal price and vat when no option is chosen', () => {
    expect(printLineValues(makeItem())).toEqual({ price: 4800, vatPct: 8, quoteUnit: '' })
  })

  it('uses the chosen option price and vat', () => {
    const item = makeItem({
      chosen_option: makeOption({ snap_price_by_volume: 4500, snap_vat: 10 }),
    })
    expect(printLineValues(item)).toEqual({ price: 4500, vatPct: 10, quoteUnit: '' })
  })

  it('falls back to the line vat when the option vat is blank (CR-058)', () => {
    const item = makeItem({
      chosen_option: makeOption({ snap_price_by_volume: 4500, snap_vat: 0 }),
    })
    expect(printLineValues(item).vatPct).toBe(8)
  })

  // H.4: ĐVT lệch thì in cả hai, KHÔNG tự quy đổi — trùng nhau thì đừng in lặp.
  it('exposes the quote unit only when it differs from the line unit', () => {
    const differs = makeItem({ chosen_option: makeOption({ snap_quote_unit: 'cuộn' }) })
    const same = makeItem({ chosen_option: makeOption({ snap_quote_unit: 'm' }) })
    expect(printLineValues(differs).quoteUnit).toBe('cuộn')
    expect(printLineValues(same).quoteUnit).toBe('')
  })

  // Góp ý khách 15/09: báo giá ghi "Cái", dòng ghi "cái" — từng in
  // "cái (báo giá: Cái)" làm gãy dòng ô ĐVT; khác mỗi hoa thường là MỘT đơn vị.
  it('ignores case-only differences between quote unit and line unit', () => {
    const item = makeItem({
      unit: 'cái',
      chosen_option: makeOption({ snap_quote_unit: 'Cái' }),
    })
    expect(printLineValues(item).quoteUnit).toBe('')
  })

  // Phương án 0 chụp đúng dòng gốc — phiếu chưa ai đụng phải in ra y như cũ.
  it('option zero mirroring the line prints exactly the old values', () => {
    const item = makeItem({
      chosen_option: makeOption({
        source: PR_OPTION_SOURCE_ORIGINAL,
        public_id: 0,
        snap_price_by_volume: 4800,
        snap_vat: 8,
        snap_quote_unit: 'm',
      }),
    })
    expect(printLineValues(item)).toEqual({ price: 4800, vatPct: 8, quoteUnit: '' })
  })

  it('treats non-numeric snapshot price as zero instead of NaN', () => {
    const item = makeItem({
      chosen_option: makeOption({
        snap_price_by_volume: 'abc' as unknown as number,
        snap_vat: 10,
      }),
    })
    expect(printLineValues(item).price).toBe(0)
  })
})

// `dominantChosenSupplier` (NCC "tối ưu nhất" tự đổ vào ô NCC chung của bản A)
// đã GỠ ở rà lại vòng 3: mục đó tên là "NCC do bộ phận đề xuất" nên chỉ in thứ
// nhập trên phiếu — NCC theo phương án xem ở bản B.

describe('buildSupplierPrintPlan — bản B soi gương luật gom của backend', () => {
  const chosenOf = (code: string, name: string, price: number, vat = 0) =>
    makeOption({ supplier_code: code, supplier_name: name, snap_price_by_volume: price, snap_vat: vat })

  it('groups lines by chosen supplier, one page per supplier', () => {
    const plan = buildSupplierPrintPlan([
      makeItem({ id: 1, chosen_option: chosenOf('A', 'NCC A', 100) }),
      makeItem({ id: 2, product_code: 'SP-B', chosen_option: chosenOf('B', 'NCC B', 200) }),
      makeItem({ id: 3, product_code: 'SP-C', chosen_option: chosenOf('A', 'NCC A', 300) }),
    ])
    expect(plan.groups).toHaveLength(2)
    const groupA = plan.groups.find((g) => g.supplierCode === 'A')
    expect(groupA?.lines).toHaveLength(2)
  })

  // Chỉ bỏ dòng hủy và dòng không chọn phương án — dòng đã lên ĐMH VẪN in
  // (góp ý khách 15/09: bản in là bản lưu, tạo đơn xong vẫn phải in lại được).
  it('skips cancelled and no-chosen lines but keeps already-ordered lines printable', () => {
    const plan = buildSupplierPrintPlan([
      makeItem({ id: 1, line_status: 'cancelled', chosen_option: chosenOf('A', 'NCC A', 100) }),
      makeItem({ id: 2, product_code: 'SP-B', line_status: 'ordered', chosen_option: chosenOf('A', 'NCC A', 100) }),
      makeItem({ id: 3, product_code: 'SP-C' }),
      makeItem({ id: 4, product_code: 'SP-D', chosen_option: chosenOf('A', 'NCC A', 100) }),
    ])
    expect(plan.skipped).toEqual({ noChosen: 1, cancelled: 1 })
    expect(plan.groups).toHaveLength(1)
    expect(plan.groups[0].lines).toHaveLength(2)
  })

  // Lỗi khách gặp 15/09: hai dòng vừa lên đơn NHÁP (CR-074 rời `no_po` ngay)
  // làm bản in ra "0 trang" — bản in KHÔNG soi luật chống trùng của nút gom.
  it('keeps printing lines that already sit on a draft order', () => {
    const plan = buildSupplierPrintPlan([
      makeItem({ id: 1, line_status: 'not_ordered', chosen_option: chosenOf('A', 'NCC A', 100) }),
      makeItem({
        id: 2,
        product_code: 'SP-B',
        line_status: '' as PurchaseRequestItem['line_status'],
        chosen_option: chosenOf('A', 'NCC A', 100),
      }),
    ])
    expect(plan.skipped).toEqual({ noChosen: 0, cancelled: 0 })
    expect(plan.groups[0].lines).toHaveLength(2)
  })

  it('collects lines whose chosen option has no supplier into one trailing group', () => {
    const plan = buildSupplierPrintPlan([
      makeItem({ id: 1, chosen_option: makeOption({ snap_price_by_volume: 100 }) }),
      makeItem({ id: 2, product_code: 'SP-B', chosen_option: chosenOf('A', 'NCC A', 200) }),
      makeItem({ id: 3, product_code: 'SP-C', chosen_option: makeOption({ snap_price_by_volume: 300 }) }),
    ])
    expect(plan.groups).toHaveLength(2)
    const last = plan.groups[plan.groups.length - 1]
    expect(last.key).toBe('')
    expect(last.lines).toHaveLength(2)
  })

  it('sorts supplier pages by name with the no-supplier group always last', () => {
    const plan = buildSupplierPrintPlan([
      makeItem({ id: 1, chosen_option: makeOption({ snap_price_by_volume: 1 }) }),
      makeItem({ id: 2, product_code: 'SP-B', chosen_option: chosenOf('Z', 'Zeta', 1) }),
      makeItem({ id: 3, product_code: 'SP-C', chosen_option: chosenOf('A', 'Án Bình', 1) }),
    ])
    expect(plan.groups.map((g) => g.supplierName || '(none)')).toEqual([
      'Án Bình',
      'Zeta',
      '(none)',
    ])
  })

  it('computes subtotal, vat amount and total per page with the CR-058 vat fallback', () => {
    const plan = buildSupplierPrintPlan([
      // VAT phương án 10% thắng VAT dòng.
      makeItem({ id: 1, qty: 10, chosen_option: chosenOf('A', 'NCC A', 100, 10) }),
      // VAT phương án bỏ trống -> rơi về VAT dòng 8%.
      makeItem({ id: 2, product_code: 'SP-B', qty: 10, chosen_option: chosenOf('A', 'NCC A', 200) }),
    ])
    const group = plan.groups[0]
    expect(group.subtotal).toBe(10 * 100 + 10 * 200)
    expect(group.total).toBeCloseTo(10 * 100 * 1.1 + 10 * 200 * 1.08)
    expect(group.vatAmount).toBeCloseTo(10 * 100 * 0.1 + 10 * 200 * 0.08)
  })

  // Rà lại vòng 4: mỗi tờ bản B là tờ PHIẾU ĐỀ XUẤT dùng chung, nó tự đọc `item`
  // bằng `printLineValues` — nên dòng gom chỉ được giữ `item` + phần tính tiền.
  // Bốn trường cũ (ĐVT báo giá, tên NCC gọi, thời gian/nơi giao) đã gỡ; giữ lại
  // là mời người sau in chúng ra một chỗ mà mẫu 003/BM/PKT không có ô.
  it('carries only the source line and its money figures, no bespoke print fields', () => {
    const plan = buildSupplierPrintPlan([
      makeItem({
        id: 1,
        qty: 10,
        chosen_option: makeOption({
          supplier_code: 'A',
          supplier_name: 'NCC A',
          snap_price_by_volume: 100,
          snap_vat: 10,
          snap_product_name: 'Greige fabric',
          snap_quote_unit: 'cuộn',
          snap_delivery_time: '7 ngày',
          snap_delivery_place: 'Kho Bình Dương',
        }),
      }),
    ])
    const [line] = plan.groups[0].lines
    expect(Object.keys(line).sort()).toEqual(['amount', 'item', 'price', 'vatPct'])
    expect(line.item.id).toBe(1)
    expect(line.amount).toBeCloseTo(10 * 100 * 1.1)
  })

  it('returns an empty plan for an empty request', () => {
    expect(buildSupplierPrintPlan([])).toEqual({
      groups: [],
      skipped: { noChosen: 0, cancelled: 0 },
    })
  })

  it('ignores placeholder rows without a product name', () => {
    const plan = buildSupplierPrintPlan([
      makeItem({ id: 1, product_name: '', chosen_option: chosenOf('A', 'NCC A', 100) }),
    ])
    expect(plan.groups).toHaveLength(0)
    expect(plan.skipped).toEqual({ noChosen: 0, cancelled: 0 })
  })
})

describe('printedTotals — tổng tiền bản A tính lại theo giá đang in', () => {
  it('recomputes totals from the printed prices, not the stored header totals', () => {
    const totals = printedTotals([
      makeItem({ qty: 10, chosen_option: makeOption({ snap_price_by_volume: 100, snap_vat: 10 }) }),
      makeItem({ product_code: 'SP-B', qty: 10 }),
    ])
    expect(totals.subtotal).toBe(10 * 100 + 10 * 4800)
    expect(totals.total).toBeCloseTo(10 * 100 * 1.1 + 10 * 4800 * 1.08)
    expect(totals.vat).toBeCloseTo(totals.total - totals.subtotal)
  })

  it('returns zeros for an empty list', () => {
    expect(printedTotals([])).toEqual({ subtotal: 0, vat: 0, total: 0 })
  })
})
