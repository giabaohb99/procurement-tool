import { describe, expect, it } from 'vitest'

import type { PurchaseRequestItem } from '../types/purchase-request-detail'
import type { PurchasingPrintData, PurchasingPrintLine } from '../types/purchasing-print'
import { buildPurchasingItemTable, buildRequestItemTable } from './purchase-request-print-rows'

function makeRequestItem(overrides: Partial<PurchaseRequestItem>): PurchaseRequestItem {
  //  why: bảng hàng chỉ đọc vài trường của dòng YCMH — dựng đủ kiểu dòng ở đây là nhiễu.
  return {
    id: 1,
    product_name: 'Hàng YCMH',
    product_code: 'MH1',
    unit: 'Cái',
    qty: 2,
    price: 1000,
    vat_pct: 10,
    warehouse: 'Kho A',
    note: 'ghi chú YCMH',
    chosen_option: null,
    ...overrides,
  } as unknown as PurchaseRequestItem
}

function makeLine(overrides: Partial<PurchasingPrintLine>): PurchasingPrintLine {
  return {
    line_id: 11,
    product_code: 'MH1',
    product_name: 'Hàng ĐMH',
    invoice_name: '',
    spec: '',
    item_group: '',
    unit: 'Thùng',
    qty: 3,
    price: 2000,
    vat: 8,
    amount: 6480,
    ...overrides,
  }
}

type TableData = Pick<PurchasingPrintData, 'items' | 'subtotal' | 'vat' | 'total' | 'currency'>

function makeData(items: PurchasingPrintLine[], overrides: Partial<TableData> = {}): TableData {
  return { items, subtotal: 6000, vat: 480, total: 6480, currency: 'VND', ...overrides }
}

describe('buildRequestItemTable', () => {
  it('keeps the old pricing: line price, qty x price, totals incl. VAT on top', () => {
    const table = buildRequestItemTable([makeRequestItem({})])
    expect(table.rows[0]).toMatchObject({ qty: 2, price: 1000, amount: 2000, warehouse: 'Kho A' })
    expect(table.totals).toEqual({ subtotal: 2000, vat: 200, total: 2200 })
    expect(table.fractionalMoney).toBe(false)
  })

  it('empty request prints zero totals, not NaN', () => {
    expect(buildRequestItemTable([]).totals).toEqual({ subtotal: 0, vat: 0, total: 0 })
  })
})

// duoc-CR-777 — bảng hàng của mẫu thu mua lấy dòng ĐƠN, tổng của máy chủ, không tính lại theo YCMH.
describe('buildPurchasingItemTable (duoc-CR-777)', () => {
  it('prints order qty / unit / price and takes totals straight from the server', () => {
    const table = buildPurchasingItemTable(makeData([makeLine({})]), [makeRequestItem({})])
    expect(table.rows[0]).toMatchObject({
      productName: 'Hàng ĐMH',
      productCode: 'MH1',
      unit: 'Thùng',
      quoteUnit: '',
      qty: 3,
      price: 2000,
    })
    expect(table.totals).toEqual({ subtotal: 6000, vat: 480, total: 6480 })
  })

  it('line amount is qty x price BEFORE VAT, never the server amount that includes VAT', () => {
    //  Cột "Thành tiền" cộng lại phải ra dòng "Tổng cộng" (trước thuế) — dùng `amount` là lệch VAT.
    const table = buildPurchasingItemTable(makeData([makeLine({ amount: 999_999 })]), [])
    expect(table.rows[0].amount).toBe(6000)
    expect(table.rows.reduce((sum, row) => sum + row.amount, 0)).toBe(table.totals.subtotal)
  })

  it('rounds line amounts to cents like the backend so the column adds up', () => {
    const table = buildPurchasingItemTable(
      makeData([makeLine({ qty: 3, price: 0.3355 })], { subtotal: 1.01, currency: 'USD' }),
      [],
    )
    expect(table.rows[0].amount).toBe(1.01)
    expect(table.fractionalMoney).toBe(true)
  })

  it('borrows delivery place and note from the request line with the same code, last match wins', () => {
    const table = buildPurchasingItemTable(makeData([makeLine({})]), [
      makeRequestItem({ id: 1, warehouse: 'Kho A', note: 'đầu' }),
      makeRequestItem({ id: 2, warehouse: 'Kho B', note: 'sau' }),
    ])
    expect(table.rows[0]).toMatchObject({ warehouse: 'Kho B', note: 'sau' })
  })

  it('unmatched or blank product codes leave place and note empty', () => {
    const table = buildPurchasingItemTable(
      makeData([makeLine({ product_code: 'KHAC' }), makeLine({ line_id: 12, product_code: '' })]),
      [makeRequestItem({ product_code: '' }), makeRequestItem({ product_code: 'MH1' })],
    )
    expect(table.rows.map((row) => [row.warehouse, row.note])).toEqual([
      ['', ''],
      ['', ''],
    ])
  })

  it('an order with no live lines prints an empty table with the server totals', () => {
    const table = buildPurchasingItemTable(makeData([], { subtotal: 0, vat: 0, total: 0 }), [
      makeRequestItem({}),
    ])
    expect(table.rows).toEqual([])
    expect(table.totals).toEqual({ subtotal: 0, vat: 0, total: 0 })
  })

  it('treats missing numbers as zero and missing currency as VND', () => {
    const table = buildPurchasingItemTable(
      {
        //  why: máy chủ cũ / dữ liệu hỏng có thể trả null — bản in không được in NaN.
        items: [makeLine({ qty: null as unknown as number, price: undefined as unknown as number })],
        subtotal: null as unknown as number,
        vat: Number.NaN,
        total: 0,
        currency: '',
      },
      [],
    )
    expect(table.rows[0]).toMatchObject({ qty: 0, price: 0, amount: 0 })
    expect(table.totals).toEqual({ subtotal: 0, vat: 0, total: 0 })
    expect(table.fractionalMoney).toBe(false)
  })

  it('keeps every row key unique even when line ids are missing', () => {
    const table = buildPurchasingItemTable(
      makeData([makeLine({ line_id: 0 }), makeLine({ line_id: 0 })]),
      [],
    )
    expect(new Set(table.rows.map((row) => row.key)).size).toBe(2)
  })
})
