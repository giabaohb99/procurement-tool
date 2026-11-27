import { describe, expect, it } from 'vitest'

import type { PurchaseOrderItem } from '../types/purchase-order-detail'
import {
  buildPriceAdjustPayload,
  isPriceAdjustAvailable,
  isPriceChanged,
  isPriceValid,
  listPriceAdjustableLines,
  receivedAmountDelta,
  type PriceAdjustLine,
} from './purchase-order-price-adjust'

function line(overrides: Partial<PurchaseOrderItem>): PurchaseOrderItem {
  return {
    id: 1,
    product_code: 'VT01',
    product_name: 'Vật tư 01',
    qty_order: 10,
    qty_received: 0,
    price: 4250,
    progress_status: 'ordered',
    deliveries: [],
    ...overrides,
  } as PurchaseOrderItem
}

function adjustable(overrides: Partial<PurchaseOrderItem>): PriceAdjustLine {
  return line(overrides) as PriceAdjustLine
}

/** bao-CR-794 — luật của hộp Sửa giá sau duyệt, bản sao của `price_adjust_service.py`. */
describe('listPriceAdjustableLines', () => {
  it('keeps saved lines that are neither completed nor cancelled', () => {
    const lines = listPriceAdjustableLines([
      line({ id: 1, progress_status: 'ordered' }),
      line({ id: 2, progress_status: 'completed' }),
      line({ id: 3, progress_status: 'cancelled' }),
      line({ id: 4, progress_status: 'paused' }),
      line({ id: 5, progress_status: undefined }),
    ])
    expect(lines.map((item) => item.id)).toEqual([1, 4, 5])
  })

  it('drops lines without a real id — the server addresses lines by id', () => {
    expect(listPriceAdjustableLines([line({ id: undefined }), line({ id: 0 })])).toEqual([])
    expect(listPriceAdjustableLines([])).toEqual([])
  })
})

describe('isPriceAdjustAvailable', () => {
  const open = [line({ id: 1 })]

  it('allows approved, partially received and fully received orders', () => {
    for (const status of ['approved', 'partial', 'received']) {
      expect(isPriceAdjustAvailable({ status, items: open })).toBe(true)
    }
  })

  it('refuses orders outside the approved stages', () => {
    for (const status of ['draft', 'submitted', 'rejected', 'completed', 'cancelled', '']) {
      expect(isPriceAdjustAvailable({ status, items: open })).toBe(false)
    }
  })

  it('refuses a received order whose every line is already completed or cancelled', () => {
    const items = [
      line({ id: 1, progress_status: 'completed' }),
      line({ id: 2, progress_status: 'cancelled' }),
    ]
    expect(isPriceAdjustAvailable({ status: 'received', items })).toBe(false)
    expect(isPriceAdjustAvailable({ status: 'received', items: [] })).toBe(false)
  })
})

describe('isPriceChanged / isPriceValid', () => {
  const item = adjustable({ id: 7, price: 1668.182 })

  it('treats an untouched line as unchanged and valid', () => {
    expect(isPriceChanged(item, {})).toBe(false)
    expect(isPriceValid(item, {})).toBe(true)
  })

  it('ignores float noise below the 4-decimal precision of a unit price', () => {
    expect(isPriceChanged(item, { 7: 1668.1820000001 })).toBe(false)
    expect(isPriceChanged(item, { 7: 1668.1821 })).toBe(true)
  })

  it('rejects zero, negative and non-finite prices', () => {
    for (const price of [0, -1, Number.NaN, Number.POSITIVE_INFINITY]) {
      expect(isPriceValid(item, { 7: price })).toBe(false)
    }
    expect(isPriceValid(item, { 7: 0.0001 })).toBe(true)
  })
})

describe('receivedAmountDelta', () => {
  it('multiplies the price difference by the RECEIVED quantity, not the ordered one', () => {
    const item = adjustable({ id: 1, qty_order: 10, qty_received: 4, price: 4250 })
    expect(receivedAmountDelta(item, { 1: 5000 })).toBe(3000)
    expect(receivedAmountDelta(item, { 1: 4000 })).toBe(-1000)
    expect(receivedAmountDelta(item, {})).toBe(0)
  })

  it('returns null for a line with nothing received yet', () => {
    expect(receivedAmountDelta(adjustable({ id: 1, qty_received: 0 }), { 1: 9999 })).toBeNull()
    expect(receivedAmountDelta(adjustable({ id: 1, qty_received: undefined }), { 1: 9999 })).toBeNull()
  })
})

describe('buildPriceAdjustPayload', () => {
  const lines = [
    adjustable({ id: 1, price: 4250 }),
    adjustable({ id: 2, price: 1350 }),
    adjustable({ id: 3, price: 99 }),
  ]

  it('sends only the lines whose price changed, with the reason trimmed', () => {
    expect(buildPriceAdjustPayload(lines, { 1: 5000, 2: 1350 }, '  NCC báo lại giá  ')).toEqual({
      reason: 'NCC báo lại giá',
      items: [{ id: 1, price: 5000 }],
    })
  })

  it('returns null without a reason or with a blank one', () => {
    expect(buildPriceAdjustPayload(lines, { 1: 5000 }, '')).toBeNull()
    expect(buildPriceAdjustPayload(lines, { 1: 5000 }, '   \n ')).toBeNull()
  })

  it('returns null when no line changed', () => {
    expect(buildPriceAdjustPayload(lines, {}, 'Lý do')).toBeNull()
    expect(buildPriceAdjustPayload(lines, { 1: 4250, 2: 1350 }, 'Lý do')).toBeNull()
    expect(buildPriceAdjustPayload([], { 1: 5000 }, 'Lý do')).toBeNull()
  })

  it('blocks the whole request while any line carries a price of zero — never drops it silently', () => {
    expect(buildPriceAdjustPayload(lines, { 1: 5000, 2: 0 }, 'Lý do')).toBeNull()
    expect(buildPriceAdjustPayload(lines, { 2: -5 }, 'Lý do')).toBeNull()
  })
})
