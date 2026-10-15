import { describe, expect, it } from 'vitest'

import { describeOrdered, findOverOrders, type LineProgress } from './over-order'

const KCL: LineProgress = {
  name: 'KCl',
  requested: 100,
  ordered: 80,
  pending: 20,
  orders: [
    { id: 1, code: 'PO1', status: 'approved', status_label: 'Đã duyệt', pending: false, qty: 80, received: 10 },
    { id: 2, code: 'PO2', status: 'draft', status_label: 'Nháp', pending: true, qty: 20, received: 0 },
  ],
}

describe('describeOrdered (bao-CR-619)', () => {
  it('lists approved orders with received qty and pending orders separately', () => {
    expect(describeOrdered(KCL)).toBe(
      'đã đặt 80 (PO1 Đã duyệt, đã nhận 10) · đang chờ duyệt 20 (PO2 Nháp)',
    )
  })

  it('omits the pending part when nothing is waiting', () => {
    expect(describeOrdered({ ordered: 0, pending: 0, orders: [] })).toBe('đã đặt 0')
  })
})

describe('findOverOrders (bao-CR-619)', () => {
  it('flags a code whose ordered + pending + this order exceeds the request, summing duplicate lines', () => {
    const over = findOverOrders(
      [
        { product_code: 'KCL', qty_order: 3 },
        { product_code: ' KCL ', qty_order: 2 },
        { product_code: 'OTHER', qty_order: 999 },
      ],
      { KCL },
    )
    expect(over).toEqual([{ code: 'KCL', progress: KCL, qty: 5, over: 5 }])
  })

  it('stays quiet when the total fits, the qty is zero, or there is no progress', () => {
    expect(findOverOrders([{ product_code: 'KCL', qty_order: 0 }], { KCL })).toEqual([])
    expect(findOverOrders([{ product_code: 'KCL', qty_order: 0.5 }], { KCL: { ...KCL, pending: 0 } })).toEqual([])
    expect(findOverOrders([{ product_code: 'KCL', qty_order: 5 }], undefined)).toEqual([])
  })
})
