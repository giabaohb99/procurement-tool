import type { PurchaseOrderPriceAdjustPayload } from '../api/purchase-order-api'
import {
  isDeliveryStage,
  isLineLocked,
  type PurchaseOrderDetail,
  type PurchaseOrderItem,
} from '../types/purchase-order-detail'

/**
 * bao-CR-794 — Sửa ĐƠN GIÁ sau duyệt. Luật ở đây là bản sao cho êm của
 * `backend/app/modules/purchase_order/price_adjust_service.py`; máy chủ vẫn kiểm lại và còn chặn
 * thêm những thứ màn hình không biết (đơn có yêu cầu thanh toán đã gửi duyệt, công nợ đã trả).
 */

/** Dòng đã lưu (có id) — hộp Sửa giá chỉ làm việc trên dòng có id thật. */
export type PriceAdjustLine = PurchaseOrderItem & { id: number }

/** Giá mới người dùng đang gõ, theo id dòng. Dòng không có mặt = chưa đụng tới. */
export type PriceAdjustDraft = Record<number, number>

/** Sai số so giá — đơn giá giữ tối đa 4 chữ số thập phân. */
const PRICE_EPSILON = 0.00005

/** Dòng còn sửa giá được: đã lưu và chưa Hoàn thành / Hủy. */
export function listPriceAdjustableLines(items: PurchaseOrderItem[]): PriceAdjustLine[] {
  return items.filter((item): item is PriceAdjustLine => Boolean(item.id) && !isLineLocked(item))
}

/**
 * Đơn có cho Sửa giá không (chưa xét quyền): Đã duyệt / Nhận một phần / Đã nhận và còn ít nhất một
 * dòng chưa chốt. Khác Hủy duyệt: đơn ĐÃ NHẬN HÀNG vẫn sửa được — đó chính là mục đích của lệnh.
 */
export function isPriceAdjustAvailable(order: Pick<PurchaseOrderDetail, 'status' | 'items'>): boolean {
  return isDeliveryStage(order.status) && listPriceAdjustableLines(order.items).length > 0
}

/** Giá mới của dòng — chưa gõ thì là giá hiện tại. */
export function draftPriceOf(line: PriceAdjustLine, draft: PriceAdjustDraft): number {
  return draft[line.id] ?? (Number(line.price) || 0)
}

export function isPriceChanged(line: PriceAdjustLine, draft: PriceAdjustDraft): boolean {
  return Math.abs(draftPriceOf(line, draft) - (Number(line.price) || 0)) > PRICE_EPSILON
}

/** Giá mới phải lớn hơn 0 (máy chủ khai `gt=0`); ô bị xóa trắng cũng tính là 0. */
export function isPriceValid(line: PriceAdjustLine, draft: PriceAdjustDraft): boolean {
  const price = draftPriceOf(line, draft)
  return Number.isFinite(price) && price > 0
}

/**
 * Chênh lệch THÀNH TIỀN CHƯA VAT theo số lượng ĐÃ NHẬN = SL đã nhận × (giá mới − giá cũ), theo
 * nguyên tệ của dòng. `null` khi dòng chưa nhận hàng: chưa có công nợ nào để chênh.
 */
export function receivedAmountDelta(line: PriceAdjustLine, draft: PriceAdjustDraft): number | null {
  const received = Number(line.qty_received) || 0
  if (received <= 0) return null
  return received * (draftPriceOf(line, draft) - (Number(line.price) || 0))
}

/**
 * Thân lệnh gửi lên: CHỈ các dòng đổi giá. Trả `null` khi chưa gửi được — thiếu lý do, không dòng
 * nào đổi giá, hoặc còn dòng mang giá không hợp lệ (để người dùng sửa, không lặng lẽ bỏ qua dòng đó).
 */
export function buildPriceAdjustPayload(
  lines: PriceAdjustLine[],
  draft: PriceAdjustDraft,
  reason: string,
): PurchaseOrderPriceAdjustPayload | null {
  const trimmed = reason.trim()
  if (!trimmed) return null
  if (lines.some((line) => !isPriceValid(line, draft))) return null
  const items = lines
    .filter((line) => isPriceChanged(line, draft))
    .map((line) => ({ id: line.id, price: draftPriceOf(line, draft) }))
  return items.length ? { reason: trimmed, items } : null
}
