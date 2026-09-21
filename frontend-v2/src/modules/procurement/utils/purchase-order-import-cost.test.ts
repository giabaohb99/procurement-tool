import { describe, expect, it } from 'vitest'

import {
  ALLOCATION_MANUAL,
  ORDER_TYPE_DOMESTIC,
  ORDER_TYPE_IMPORT,
  STATE_BUDGET_SUPPLIER_CODE,
  STATE_BUDGET_SUPPLIER_NAME,
  type PurchaseOrderDetail,
  type PurchaseOrderImportCost,
  type PurchaseOrderItem,
} from '../types/purchase-order-detail'
import { createEmptyImportCost, createEmptyPurchaseOrder } from './purchase-order-draft'
import {
  applyCostType,
  costBaseAmount,
  displayCostBaseAmount,
  displayLineBaseAmount,
  effectiveExchangeRate,
  groupCostsBySupplier,
  groupCostsByType,
  isMissingExchangeRate,
  lineBaseAmount,
  manualAllocationGap,
  manualAllocationTotal,
  paymentBlockReason,
  percentOf,
  resolveTotalsCurrency,
  setManualAllocation,
  summarizeOrderTotals,
  switchAllocationMethod,
  switchOrderType,
} from './purchase-order-import-cost'

function cost(overrides: Partial<PurchaseOrderImportCost> = {}): PurchaseOrderImportCost {
  return { ...createEmptyImportCost(), ...overrides }
}

function line(): PurchaseOrderItem {
  return {
    product_code: 'SP01',
    product_name: 'Hàng A',
    invoice_name: '',
    item_group: '',
    spec: '',
    fg_code: '',
    fg_name: '',
    invoice_no: '',
    invoice_date: '',
    document_delivery_date: '',
    supplier_ready: true,
    required_date: '',
    expected_date: '',
    unit: 'cái',
    qty_request: 1,
    qty_order: 1,
    price: 1,
    vat: 0,
    warehouse_code: '',
    note: '',
    currency: '',
    exchange_rate: 0,
    weight_kg: 0,
    dimension: '',
    deliveries: [],
  }
}

function importOrder(overrides: Partial<PurchaseOrderDetail> = {}): PurchaseOrderDetail {
  return {
    ...createEmptyPurchaseOrder(),
    order_type: ORDER_TYPE_IMPORT,
    currency: 'USD',
    exchange_rate: 25_000,
    ...overrides,
  }
}

describe('effectiveExchangeRate', () => {
  it('treats VND as rate 1 no matter what rate was typed', () => {
    expect(effectiveExchangeRate('VND', 25_000)).toBe(1)
    expect(effectiveExchangeRate('', 0)).toBe(1)
    expect(effectiveExchangeRate('vnd', -3)).toBe(1)
  })

  it('returns 0 for a foreign currency without a usable rate so nothing is silently converted at 1:1', () => {
    expect(effectiveExchangeRate('USD', 0)).toBe(0)
    expect(effectiveExchangeRate('USD', Number.NaN)).toBe(0)
    expect(effectiveExchangeRate('USD', -1)).toBe(0)
    expect(effectiveExchangeRate('USD', 25_000.5)).toBe(25_000.5)
  })
})

describe('lineBaseAmount', () => {
  it('falls back to the order currency and rate when the line leaves them blank', () => {
    const order = importOrder()
    const line = { qty_order: 10, price: 2, vat: 0, currency: '', exchange_rate: 0 }
    expect(lineBaseAmount(line, order)).toBe(10 * 2 * 25_000)
  })

  it('prefers the line rate over the order rate and applies line VAT', () => {
    const order = importOrder()
    const line = { qty_order: 1, price: 100, vat: 10, currency: 'USD', exchange_rate: 24_000 }
    expect(lineBaseAmount(line, order)).toBeCloseTo(100 * 1.1 * 24_000, 6)
  })

  it('yields 0 for a foreign line whose rate is still missing on both levels', () => {
    const order = importOrder({ exchange_rate: 0 })
    expect(lineBaseAmount({ qty_order: 5, price: 5, vat: 0, currency: '', exchange_rate: 0 }, order)).toBe(0)
  })
})

describe('costBaseAmount', () => {
  it('includes VAT and converts by the cost own rate', () => {
    expect(costBaseAmount(cost({ amount: 100, vat: 8, currency: 'USD', exchange_rate: 25_000 }))).toBeCloseTo(
      100 * 1.08 * 25_000,
      6,
    )
    expect(costBaseAmount(cost({ amount: 1_000_000, vat: 0, currency: 'VND' }))).toBe(1_000_000)
  })
})

describe('applyCostType', () => {
  it('fills the state budget supplier for a tax cost when the supplier is blank', () => {
    const next = applyCostType(cost(), 4)
    expect(next.supplier_code).toBe(STATE_BUDGET_SUPPLIER_CODE)
    expect(next.supplier_name).toBe(STATE_BUDGET_SUPPLIER_NAME)
  })

  it('keeps a real supplier the user already picked even for a tax cost', () => {
    const next = applyCostType(cost({ supplier_code: 'NCC001', supplier_name: 'Khai thuê A' }), 5)
    expect(next.supplier_code).toBe('NCC001')
  })

  // Lỗi dễ dính: chọn Thuế nhập khẩu xong đổi lại thành Cước tàu — nếu giữ NSNN thì
  // cước tàu ghi nợ cho nhà nước.
  it('clears the state budget supplier when switching from a tax cost to an ordinary one', () => {
    const taxed = applyCostType(cost(), 4)
    const next = applyCostType(taxed, 1)
    expect(next.supplier_code).toBe('')
    expect(next.supplier_name).toBe('')
  })
})

describe('manual allocation', () => {
  it('sums typed shares and ignores garbage values', () => {
    const c = cost({
      allocation_method: ALLOCATION_MANUAL,
      manual_allocation: { '1': 100, '2': 50.5, '3': Number.NaN },
    })
    expect(manualAllocationTotal(c)).toBe(150.5)
  })

  it('reports no gap inside the 1 VND tolerance and the exact gap outside it', () => {
    const c = cost({
      amount: 1000,
      vat: 0,
      currency: 'VND',
      allocation_method: ALLOCATION_MANUAL,
      manual_allocation: { '1': 600, '2': 399.5 },
    })
    expect(manualAllocationGap(c)).toBe(0)
    expect(manualAllocationGap({ ...c, manual_allocation: { '1': 600 } })).toBe(400)
  })

  it('removes the key instead of storing 0 or NaN', () => {
    const c = setManualAllocation(cost({ manual_allocation: { '7': 10 } }), 7, 0)
    expect(c.manual_allocation).toEqual({})
    expect(setManualAllocation(c, 8, Number.NaN).manual_allocation).toEqual({})
    expect(setManualAllocation(c, 8, 12.5).manual_allocation).toEqual({ '8': 12.5 })
  })
})

describe('display base amounts', () => {
  it('prefers the stored base amount and only computes when the backend has not saved one', () => {
    const order = importOrder()
    const saved = { ...line(), qty_order: 10, price: 2, base_amount: 123_456 }
    expect(displayLineBaseAmount(saved, order)).toBe(123_456)
    const draft = { ...line(), qty_order: 10, price: 2, base_amount: 0 }
    expect(displayLineBaseAmount(draft, order)).toBe(10 * 2 * 25_000)
    expect(displayLineBaseAmount({ ...draft, base_amount: undefined }, order)).toBe(10 * 2 * 25_000)
  })

  it('does the same for a cost line', () => {
    expect(displayCostBaseAmount(cost({ amount: 100, currency: 'VND', base_amount: 999 }))).toBe(999)
    expect(displayCostBaseAmount(cost({ amount: 100, currency: 'VND', base_amount: 0 }))).toBe(100)
  })
})

describe('isMissingExchangeRate', () => {
  // Lỗi bao-CR-319: đơn USD chưa có tỷ giá từng hiện "Quy đổi 0 đ" thay vì nói thiếu tỷ giá.
  it('flags a foreign line when neither the line nor the order has a rate', () => {
    const order = importOrder({ exchange_rate: 0 })
    expect(isMissingExchangeRate({ currency: '', exchange_rate: 0 }, order)).toBe(true)
    expect(isMissingExchangeRate({ currency: 'USD', exchange_rate: 0 }, order)).toBe(true)
  })

  it('is satisfied by a rate on either level and never flags VND', () => {
    expect(isMissingExchangeRate({ currency: '', exchange_rate: 0 }, importOrder())).toBe(false)
    expect(
      isMissingExchangeRate({ currency: 'USD', exchange_rate: 24_000 }, importOrder({ exchange_rate: 0 })),
    ).toBe(false)
    expect(
      isMissingExchangeRate({ currency: 'VND', exchange_rate: 0 }, importOrder({ exchange_rate: 0 })),
    ).toBe(false)
    expect(
      isMissingExchangeRate({ currency: '', exchange_rate: 0 }, { currency: '', exchange_rate: 0 }),
    ).toBe(false)
  })
})

describe('grouping costs', () => {
  it('groups by type, sums converted amounts and sorts the biggest group first', () => {
    const groups = groupCostsByType([
      cost({ cost_type: 1, amount: 100, currency: 'VND' }),
      cost({ cost_type: 4, amount: 5_000, currency: 'VND', cost_type_label: 'Thuế NK' }),
      cost({ cost_type: 1, amount: 200, currency: 'VND' }),
    ])
    expect(groups.map((group) => [group.cost_type, group.count, group.base_amount])).toEqual([
      [4, 1, 5_000],
      [1, 2, 300],
    ])
    expect(groups[0].label).toBe('Thuế NK')
  })

  it('puts costs without a supplier into one blank group instead of dropping them', () => {
    const groups = groupCostsBySupplier([
      cost({ supplier_code: '', amount: 10, currency: 'VND' }),
      cost({ supplier_code: 'NCC1', supplier_name: 'A', amount: 5, currency: 'VND' }),
      cost({ supplier_code: '', amount: 20, currency: 'VND' }),
    ])
    expect(groups).toHaveLength(2)
    const blank = groups.find((group) => group.supplier_code === '')
    expect(blank).toMatchObject({ count: 2, base_amount: 30 })
  })

  it('returns nothing for an empty list', () => {
    expect(groupCostsByType([])).toEqual([])
    expect(groupCostsBySupplier([])).toEqual([])
  })
})

describe('percentOf', () => {
  it('never divides by zero or a negative whole', () => {
    expect(percentOf(50, 0)).toBe(0)
    expect(percentOf(50, -10)).toBe(0)
    expect(percentOf(50, Number.NaN)).toBe(0)
    expect(percentOf(50, 200)).toBe(25)
    expect(percentOf(0, 200)).toBe(0)
  })
})

describe('paymentBlockReason', () => {
  const payable = cost({
    id: 9,
    supplier_code: 'NCC1',
    amount: 100,
    payable_id: 77,
    remaining: 100,
  })

  it('explains, in order, why a cost cannot be ticked for a payment request', () => {
    expect(paymentBlockReason(cost({ supplier_code: 'NCC1', amount: 1 }), true)).toBe(
      'Chưa thành công nợ (dòng mới chưa Lưu)',
    )
    expect(paymentBlockReason({ ...payable, supplier_code: '' }, true)).toBe(
      'Chưa thành công nợ (chưa chọn NCC hoặc số tiền 0)',
    )
    expect(paymentBlockReason({ ...payable, amount: 0 }, true)).toBe(
      'Chưa thành công nợ (chưa chọn NCC hoặc số tiền 0)',
    )
    expect(paymentBlockReason(payable, false)).toBe('Chưa thành công nợ (đơn chưa duyệt)')
    expect(paymentBlockReason({ ...payable, payable_id: undefined }, true)).toBe('Chưa thành công nợ')
    expect(paymentBlockReason({ ...payable, remaining: 0.005 }, true)).toBe('Đã chi đủ')
  })

  it('allows the tick only when a payable still has money to pay', () => {
    expect(paymentBlockReason(payable, true)).toBeNull()
    expect(paymentBlockReason({ ...payable, remaining: undefined }, true)).toBe('Đã chi đủ')
  })
})

describe('switchAllocationMethod', () => {
  const lines = [
    { item_id: 1, costs: [{ cost_id: 5, base_amount: 600.4 }] },
    { item_id: 2, costs: [{ cost_id: 5, base_amount: 399.6 }] },
    { item_id: 3, costs: [{ cost_id: 6, base_amount: 50 }] },
  ]

  it('prefills manual shares from the saved allocation of that same cost, rounded to the dong', () => {
    const next = switchAllocationMethod(cost({ id: 5 }), ALLOCATION_MANUAL, lines)
    expect(next.allocation_method).toBe(ALLOCATION_MANUAL)
    expect(next.manual_allocation).toEqual({ '1': 600, '2': 400 })
  })

  it('keeps shares the user already typed and does nothing special for other methods', () => {
    const typed = cost({ id: 5, manual_allocation: { '1': 1 } })
    expect(switchAllocationMethod(typed, ALLOCATION_MANUAL, lines).manual_allocation).toEqual({ '1': 1 })
    const other = switchAllocationMethod(cost({ id: 5 }), 2, lines)
    expect(other.allocation_method).toBe(2)
    expect(other.manual_allocation).toEqual({})
  })

  it('leaves an unsaved cost with no shares because it has no id to match', () => {
    expect(switchAllocationMethod(cost(), ALLOCATION_MANUAL, lines).manual_allocation).toEqual({})
    expect(switchAllocationMethod(cost({ id: 5 }), ALLOCATION_MANUAL, []).manual_allocation).toEqual({})
  })
})

describe('switchOrderType', () => {
  it('zeroes line VAT when switching to import', () => {
    const order = createEmptyPurchaseOrder()
    order.items = [
      { ...line(), vat: 8 },
      { ...line(), vat: 10 },
    ]
    const next = switchOrderType(order, ORDER_TYPE_IMPORT)
    expect(next.order_type).toBe(ORDER_TYPE_IMPORT)
    expect(next.items?.every((item) => item.vat === 0)).toBe(true)
  })

  it('resets currency, customs data and import costs when switching back to domestic', () => {
    const order = importOrder({
      customs_decl_no: 'TK-1',
      customs_decl_date: '2026-09-01',
      import_costs: [cost({ amount: 5 })],
    })
    const next = switchOrderType(order, ORDER_TYPE_DOMESTIC)
    expect(next).toMatchObject({
      order_type: ORDER_TYPE_DOMESTIC,
      currency: 'VND',
      exchange_rate: 1,
      customs_decl_no: '',
      customs_decl_date: '',
      import_costs: [],
    })
  })
})

/**
 * bao-CR-364 (port v2). Lỗi đã gặp trên prod (PO00122): đầu phiếu VND, dòng duy nhất
 * USD × 26.500 — bảng tổng in "6.500 VND" ngay trên "Quy đổi 172.250.000 đ".
 */
describe('resolveTotalsCurrency', () => {
  it('labels the totals with the line currency, not the header currency', () => {
    expect(resolveTotalsCurrency(['USD'], 'VND')).toEqual({ currency: 'USD', mixed: false })
  })

  it('falls back to the header currency for blank lines and treats VND header as VND', () => {
    expect(resolveTotalsCurrency(['', null, undefined], 'VND')).toEqual({
      currency: 'VND',
      mixed: false,
    })
    expect(resolveTotalsCurrency([], '')).toEqual({ currency: 'VND', mixed: false })
  })

  it('ignores case and whitespace so "usd" and "USD " are one currency', () => {
    expect(resolveTotalsCurrency(['usd', 'USD ', ' Usd'], 'vnd')).toEqual({
      currency: 'USD',
      mixed: false,
    })
  })

  it('flags mixed currencies and returns the header currency as the label', () => {
    expect(resolveTotalsCurrency(['USD', 'VND'], 'VND')).toEqual({ currency: 'VND', mixed: true })
    // Dòng trống theo đầu phiếu (VND) + dòng USD = hai loại tiền.
    expect(resolveTotalsCurrency(['', 'USD'], 'VND')).toEqual({ currency: 'VND', mixed: true })
  })
})

describe('summarizeOrderTotals', () => {
  it('sums in the line currency when every line shares one currency', () => {
    const order = importOrder({
      currency: 'VND',
      exchange_rate: 1,
      items: [
        { ...line(), qty_order: 10, price: 500, vat: 0, currency: 'USD', exchange_rate: 26500 },
        { ...line(), qty_order: 1, price: 1500, vat: 0, currency: 'usd', exchange_rate: 26500 },
      ],
    })
    expect(summarizeOrderTotals(order)).toEqual({
      subtotal: 6500,
      vat: 0,
      total: 6500,
      currency: 'USD',
      mixed: false,
    })
  })

  it('converts every line by its own rate when currencies are mixed', () => {
    const order = importOrder({
      currency: 'VND',
      exchange_rate: 1,
      items: [
        { ...line(), qty_order: 1, price: 100, vat: 0, currency: 'USD', exchange_rate: 25000 },
        { ...line(), qty_order: 2, price: 1000, vat: 10, currency: '', exchange_rate: 0 },
      ],
    })
    const totals = summarizeOrderTotals(order)
    expect(totals.mixed).toBe(true)
    expect(totals.currency).toBe('VND')
    // 100 × 25.000 + 2 × 1.000 = 2.502.000 chưa VAT; VAT 10% của dòng VND = 200.
    expect(totals.subtotal).toBe(2_502_000)
    expect(totals.vat).toBeCloseTo(200, 6)
    expect(totals.total).toBeCloseTo(2_502_200, 6)
  })

  it('prefers the stored base_amount of a line when the order is mixed', () => {
    const order = importOrder({
      currency: 'VND',
      exchange_rate: 1,
      items: [
        { ...line(), qty_order: 1, price: 100, currency: 'USD', exchange_rate: 25000, base_amount: 2_600_000 },
        { ...line(), qty_order: 1, price: 1000, currency: 'VND', exchange_rate: 1 },
      ],
    })
    expect(summarizeOrderTotals(order).total).toBe(2_601_000)
  })

  it('drops a foreign line without any rate to zero instead of adding raw USD to VND', () => {
    // Dòng USD không tỷ giá thì mượn tỷ giá ĐƠN (luật `resolveLineCurrency`); đơn cũng
    // không có thì dòng đó quy đổi = 0 và màn hình cảnh báo "chưa có tỷ giá" riêng.
    const order = importOrder({
      currency: 'VND',
      exchange_rate: 0,
      items: [
        { ...line(), qty_order: 1, price: 100, currency: 'USD', exchange_rate: 0 },
        { ...line(), qty_order: 1, price: 1000, currency: 'VND', exchange_rate: 1 },
      ],
    })
    const totals = summarizeOrderTotals(order)
    expect(totals.mixed).toBe(true)
    expect(totals.total).toBe(1000)
  })

  it('returns zeros and the header currency for an order with no lines', () => {
    expect(summarizeOrderTotals(importOrder({ currency: 'EUR', items: [] }))).toEqual({
      subtotal: 0,
      vat: 0,
      total: 0,
      currency: 'EUR',
      mixed: false,
    })
  })
})
