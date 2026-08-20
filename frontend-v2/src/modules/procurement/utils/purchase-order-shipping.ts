import type { PurchaseOrderItem } from '../types/purchase-order-detail'

export interface ShippingSummary {
  /** Tổng cước ghi ở các lần giao — bằng đúng `shipping_total` backend trả về. */
  total: number
  /** Số lần giao CÓ ghi cước. Trả lời câu "số tiền cước này ở đâu ra". */
  chargedCount: number
  /**
   * Số lần giao có cước nhưng CHƯA chọn đơn vị vận chuyển.
   *
   * Đây là chỗ tiền lặng lẽ rơi mất: `purchase_order/service.py` chỉ lập công nợ
   * vận chuyển khi lần giao có `carrier_code`, nên cước ghi mà bỏ trống nhà xe
   * thì vẫn cộng vào con số hiển thị nhưng KHÔNG thành khoản phải trả cho ai
   * cả — nhìn đơn tưởng đã ghi nhận, mở công nợ lại không thấy đâu.
   */
  missingCarrierCount: number
}

/** Gom số liệu cước vận chuyển của cả đơn từ các lần giao của từng dòng hàng. */
export function summarizeShipping(items: PurchaseOrderItem[]): ShippingSummary {
  const summary: ShippingSummary = { total: 0, chargedCount: 0, missingCarrierCount: 0 }

  items.forEach((item) => {
    ;(item.deliveries ?? []).forEach((delivery) => {
      const amount = Number(delivery.shipping_amount) || 0
      if (amount <= 0) return
      summary.total += amount
      summary.chargedCount += 1
      if (!delivery.carrier_code) summary.missingCarrierCount += 1
    })
  })

  summary.total = Math.round(summary.total * 100) / 100
  return summary
}
