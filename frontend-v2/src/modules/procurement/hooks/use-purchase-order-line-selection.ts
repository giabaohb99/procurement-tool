import { useLineSelection } from '@/shared/hooks/use-line-selection'

import { isLineLocked, type PurchaseOrderItem } from '../types/purchase-order-detail'

//  Khóa dòng: dòng chưa lưu chưa có id nên lấy chỉ số — khai cấp module để tham chiếu không đổi.
export function purchaseOrderRowKey(item: PurchaseOrderItem, index: number): string | number {
  return item.id ?? `new-${index}`
}

function isLineUnlocked(item: PurchaseOrderItem): boolean {
  return !isLineLocked(item)
}

/**
 * Tick nhiều dòng hàng ĐMH để "Xóa đã chọn" (bao-CR-547).
 *
 * duoc-CR-737: trạng thái chọn nhấc lên TRANG (trước nằm trong `PurchaseOrderItemsTable`)
 * vì nút *Xóa đã chọn (n)* dời lên góc phải tiêu đề thẻ *Dòng hàng* như bản v1 — nút và
 * cột tick ở hai component khác nhau nên phải chung một nguồn. Dòng đã hoàn thành / đã
 * hủy khóa như nút xóa từng dòng.
 */
export function usePurchaseOrderLineSelection(items: PurchaseOrderItem[], enabled: boolean) {
  return useLineSelection({
    rows: items,
    rowKey: purchaseOrderRowKey,
    enabled,
    isSelectable: isLineUnlocked,
    unselectableReason: 'Dòng đã hoàn thành hoặc đã hủy — không xóa được',
  })
}
