import { describe, expect, it } from 'vitest'

import type { PurchaseOrderItem } from '../types/purchase-order-detail'
import { findDeliveryAttachTarget } from './delivery-attach-target'

function item(id: number, deliveries: { id?: number; delivery_no: number }[]): PurchaseOrderItem {
  return { id, deliveries } as unknown as PurchaseOrderItem
}

const items = [
  item(11, [{ id: 800, delivery_no: 1 }]),
  item(12, [
    { id: 801, delivery_no: 1 },
    { id: 805, delivery_no: 2 },
    { delivery_no: 3 }, // lần giao chưa lưu
  ]),
]

/** ai-CR-240 — link trợ lý AI chỉ tới lần giao cần đính tệp. */
describe('findDeliveryAttachTarget', () => {
  it('tìm theo id lần giao', () => {
    const target = findDeliveryAttachTarget(items, { deliveryId: 801, lineId: 0, deliveryNo: 0 })
    expect(target.lineIndex).toBe(1)
    expect(target.delivery?.id).toBe(801)
  })

  it('tìm theo dòng + số thứ tự lần giao (lần giao trợ lý vừa thêm)', () => {
    const target = findDeliveryAttachTarget(items, { deliveryId: 0, lineId: 12, deliveryNo: 2 })
    expect(target).toMatchObject({ lineIndex: 1, delivery: { id: 805 } })
  })

  it('lần giao chưa lưu / không tồn tại: chỉ trả dòng', () => {
    expect(findDeliveryAttachTarget(items, { deliveryId: 0, lineId: 12, deliveryNo: 3 })).toEqual({
      lineIndex: 1,
      delivery: null,
    })
    expect(findDeliveryAttachTarget(items, { deliveryId: 0, lineId: 11, deliveryNo: 0 }).delivery).toBeNull()
  })

  it('id lạ: không thấy gì', () => {
    expect(findDeliveryAttachTarget(items, { deliveryId: 999, lineId: 0, deliveryNo: 0 })).toEqual({
      lineIndex: -1,
      delivery: null,
    })
  })
})
