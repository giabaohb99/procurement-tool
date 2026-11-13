import type { PurchaseOrderDelivery, PurchaseOrderItem } from '../types/purchase-order-detail'

/**
 * Tham số link trợ lý AI gửi tới màn chi tiết ĐMH (ai-CR-237 / ai-CR-240), dựng ở backend bằng
 * `assistant/tools/attach_link.build_attach_url`:
 * - `delivery` = id lần giao có sẵn;
 * - `line` = id dòng hàng, kèm `delivery_no` = số thứ tự lần giao của dòng (lần giao trợ lý vừa thêm).
 */
export interface DeliveryFocusParams {
  deliveryId: number
  lineId: number
  deliveryNo: number
}

export interface DeliveryAttachTarget {
  /** Chỉ số dòng hàng trong đơn; -1 = không thấy. */
  lineIndex: number
  /** Lần giao ĐÃ LƯU (có id) cần đính tệp; `null` = chỉ biết dòng. */
  delivery: (PurchaseOrderDelivery & { id: number }) | null
}

/** Dò dòng hàng + lần giao mà link chỉ tới. Không thấy lần giao (chưa ghi, đã xóa) thì vẫn trả dòng nếu thấy dòng. */
export function findDeliveryAttachTarget(
  items: PurchaseOrderItem[],
  { deliveryId, lineId, deliveryNo }: DeliveryFocusParams,
): DeliveryAttachTarget {
  const lineIndex = items.findIndex(
    (item) =>
      (lineId > 0 && item.id === lineId) ||
      (deliveryId > 0 && (item.deliveries ?? []).some((delivery) => delivery.id === deliveryId)),
  )
  if (lineIndex < 0) return { lineIndex, delivery: null }
  const deliveries = items[lineIndex].deliveries ?? []
  const delivery =
    deliveryId > 0
      ? deliveries.find((current) => current.id === deliveryId)
      : deliveryNo > 0
        ? deliveries.find((current) => current.delivery_no === deliveryNo)
        : undefined
  return {
    lineIndex,
    delivery: delivery?.id ? (delivery as PurchaseOrderDelivery & { id: number }) : null,
  }
}
