import { describe, expect, it } from 'vitest'
import type { PurchaseOrderItem } from '../types/purchase-order-detail'
import {
  applyRepriceDraft,
  collectRepriceLines,
  findLinesBelowReceived,
  summarizeReprice,
  updateRepriceDraft,
  updateRepriceDraftFromItems,
} from './purchase-order-reprice'

function line(id: number | undefined, qty: number, price: number, vat: number): PurchaseOrderItem {
  return { id, qty_order: qty, price, vat, order_total: 999 } as PurchaseOrderItem
}

describe('purchase order reprice draft', () => {
  const a = line(1, 10, 1000, 8)
  const b = line(2, 5, 2000, 10)

  it('drops a line from the draft when edited back to its saved value', () => {
    const edited = updateRepriceDraft({}, a, { qty_order: 10, price: 1200, vat: 8 })
    expect(Object.keys(edited)).toEqual(['1'])
    const reverted = updateRepriceDraft(edited, a, { qty_order: 10, price: 1000, vat: 8 })
    expect(reverted).toEqual({})
  })

  it('treats float noise below the server threshold as unchanged', () => {
    expect(updateRepriceDraft({}, a, { qty_order: 10, price: 1000.0000001, vat: 8 })).toEqual({})
  })

  it('ignores unsaved lines because the server can only reprice lines that have an id', () => {
    const unsaved = line(undefined, 1, 1, 0)
    expect(updateRepriceDraft({}, unsaved, { qty_order: 2, price: 2, vat: 0 })).toEqual({})
  })

  it('overlays draft values and clears the stale server order total', () => {
    const shown = applyRepriceDraft([a, b], { 1: { qty_order: 10, price: 1200, vat: 8 } })
    expect(shown[0].price).toBe(1200)
    expect(shown[0].order_total).toBeUndefined()
    expect(shown[1]).toBe(b)
  })

  it('collects only changed lines with all three numbers', () => {
    const draft = updateRepriceDraftFromItems({}, [a, b], [
      { ...a, vat: 10 },
      { ...b },
    ])
    expect(collectRepriceLines([a, b], draft)).toEqual([{ id: 1, qty_order: 10, price: 1000, vat: 10 }])
  })

  it('does not send the typed after-VAT helper field to the server', () => {
    const draft = updateRepriceDraft({}, a, { qty_order: 10, price: 1111.1111, vat: 8, price_after_vat_input: 1200 })
    expect(collectRepriceLines([a], draft)[0]).not.toHaveProperty('price_after_vat_input')
  })

  it('summarizes old and new order totals with the same formula as the amount column', () => {
    const draft = updateRepriceDraft({}, a, { qty_order: 10, price: 1200, vat: 8 })
    const summary = summarizeReprice([a, b], draft)
    expect(summary.changedCount).toBe(1)
    expect(summary.oldTotal).toBeCloseTo(10 * 1000 * 1.08 + 5 * 2000 * 1.1)
    expect(summary.newTotal).toBeCloseTo(10 * 1200 * 1.08 + 5 * 2000 * 1.1)
  })

  it('handles an empty order and non-numeric junk without NaN', () => {
    expect(summarizeReprice([], {})).toEqual({ changedCount: 0, oldTotal: 0, newTotal: 0 })
    const junk = updateRepriceDraft({}, a, {
      qty_order: Number.NaN,
      price: Number.POSITIVE_INFINITY,
      vat: 8,
    })
    expect(junk[1]).toEqual({ qty_order: 0, price: 0, vat: 8, price_after_vat_input: undefined })
  })
})

describe('quantity below received guard', () => {
  it('flags only edited lines whose new order quantity drops under what was received', () => {
    const received = { ...line(1, 300, 22000, 8), product_code: 'THC0146', qty_received: 300 } as PurchaseOrderItem
    const untouched = { ...line(2, 5, 1, 0), qty_received: 9 } as PurchaseOrderItem
    expect(findLinesBelowReceived([received, untouched], {})).toEqual([])
    const draft = updateRepriceDraft({}, received, { qty_order: 250, price: 22000, vat: 8 })
    expect(findLinesBelowReceived([received, untouched], draft)).toEqual(['THC0146'])
    const equal = updateRepriceDraft({}, received, { qty_order: 300, price: 23000, vat: 8 })
    expect(findLinesBelowReceived([received], equal)).toEqual([])
  })
})
