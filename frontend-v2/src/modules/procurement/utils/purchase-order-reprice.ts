import type { PurchaseOrderRepriceLine } from '../api/purchase-order-api'
import type { PurchaseOrderItem } from '../types/purchase-order-detail'

/**
 * Sửa giá sau duyệt của ĐMH — bản nháp GIÁ tách riêng khỏi bản nháp của đơn.
 *
 * Đơn đã duyệt vẫn có bản nháp riêng cho các ô sửa sau duyệt (ghi chú, kho, ngày giao chứng từ…) và đi
 * đường Lưu chung — đường đó máy chủ khóa giá (CR-108). Giá đi đường riêng `POST /reprice`, nên giữ ở
 * một bản nháp khác, khóa theo `item.id`: dòng chưa lưu không có id thì cũng không thể sửa giá sau duyệt.
 */

/** Ba ô lưu xuống máy chủ; ô Đơn giá sau VAT tính ra từ hai ô kia (`utils/vat-price.ts`). */
export const REPRICE_FIELDS = ['qty_order', 'price', 'vat'] as const
export type RepriceField = (typeof REPRICE_FIELDS)[number]

export interface RepriceLineDraft {
  qty_order: number
  price: number
  vat: number
  /** Số người gõ ở ô sau VAT — giữ để ô hiện đúng số đã gõ, không gửi lên máy chủ. */
  price_after_vat_input?: number
}

export type RepriceDraft = Record<number, RepriceLineDraft>

/** Cùng ngưỡng với `_differs` của máy chủ — lệch nhỏ hơn thế là cùng một số. */
const EPSILON = 1e-6

function toNumber(value: unknown): number {
  const number = Number(value)
  return Number.isFinite(number) ? number : 0
}

export function isRepriceFieldChanged(
  original: Pick<PurchaseOrderItem, RepriceField>,
  current: Pick<PurchaseOrderItem, RepriceField>,
  field: RepriceField,
): boolean {
  return Math.abs(toNumber(original[field]) - toNumber(current[field])) > EPSILON
}

export function isRepriceLineChanged(
  original: Pick<PurchaseOrderItem, RepriceField>,
  current: Pick<PurchaseOrderItem, RepriceField>,
): boolean {
  return REPRICE_FIELDS.some((field) => isRepriceFieldChanged(original, current, field))
}

/**
 * Dòng đang hiện = dòng đã lưu đè ba ô giá của bản nháp (nếu có). Bỏ `order_total` máy chủ tính sẵn: hộp
 * chi tiết dòng đọc nó trước công thức, giữ lại là ô Tổng tiền đặt hàng đứng yên ở số cũ.
 */
export function applyRepriceDraft(items: PurchaseOrderItem[], draft: RepriceDraft): PurchaseOrderItem[] {
  return items.map((item) => {
    const line = item.id ? draft[item.id] : undefined
    return line ? { ...item, ...line, order_total: undefined } : item
  })
}

/**
 * Ghi lại phần giá của một dòng vừa sửa. Sửa về đúng số cũ thì bỏ dòng khỏi bản nháp — nếu không thanh
 * đáy cứ đếm "đã sửa 1 dòng" cho một dòng nhìn y nguyên.
 */
export function updateRepriceDraft(
  draft: RepriceDraft,
  original: PurchaseOrderItem,
  next: Pick<PurchaseOrderItem, RepriceField | 'price_after_vat_input'>,
): RepriceDraft {
  if (!original.id) return draft
  const line: RepriceLineDraft = {
    qty_order: toNumber(next.qty_order),
    price: toNumber(next.price),
    vat: toNumber(next.vat),
    price_after_vat_input: next.price_after_vat_input,
  }
  const rest = { ...draft }
  delete rest[original.id]
  return isRepriceLineChanged(original, line) ? { ...rest, [original.id]: line } : rest
}

/** Danh sách đổi từ bảng: lấy phần giá của mọi dòng có id rồi ghi vào bản nháp. */
export function updateRepriceDraftFromItems(
  draft: RepriceDraft,
  originals: PurchaseOrderItem[],
  nextItems: PurchaseOrderItem[],
): RepriceDraft {
  const byId = new Map(originals.filter((item) => item.id).map((item) => [item.id, item]))
  return nextItems.reduce((acc, next) => {
    const original = next.id ? byId.get(next.id) : undefined
    return original ? updateRepriceDraft(acc, original, next) : acc
  }, draft)
}

/** Dòng gửi lên `POST /reprice` — chỉ dòng có đổi, đủ ba số. */
export function collectRepriceLines(
  originals: PurchaseOrderItem[],
  draft: RepriceDraft,
): PurchaseOrderRepriceLine[] {
  return originals.flatMap((item) => {
    const line = item.id ? draft[item.id] : undefined
    if (!item.id || !line || !isRepriceLineChanged(item, line)) return []
    return [{ id: item.id, qty_order: line.qty_order, price: line.price, vat: line.vat }]
  })
}

function orderAmount(item: Pick<PurchaseOrderItem, RepriceField>): number {
  return toNumber(item.qty_order) * toNumber(item.price) * (1 + toNumber(item.vat) / 100)
}

export interface RepriceSummary {
  changedCount: number
  oldTotal: number
  newTotal: number
}

/** Tổng tiền đặt hàng trước / sau — cùng công thức ô Thành tiền của bảng dòng. */
export function summarizeReprice(originals: PurchaseOrderItem[], draft: RepriceDraft): RepriceSummary {
  const current = applyRepriceDraft(originals, draft)
  return {
    changedCount: collectRepriceLines(originals, draft).length,
    oldTotal: originals.reduce((sum, item) => sum + orderAmount(item), 0),
    newTotal: current.reduce((sum, item) => sum + orderAmount(item), 0),
  }
}

/** SL đặt mới nhỏ hơn SL đã nhận — máy chủ chặn, giao diện báo ngay tại ô cho khỏi phải bấm Lưu mới biết. */
export function isQtyBelowReceived(item: Pick<PurchaseOrderItem, 'qty_order' | 'qty_received'>): boolean {
  return toNumber(item.qty_order) + EPSILON < toNumber(item.qty_received)
}

/** Tên các dòng đang sửa có SL đặt dưới SL đã nhận (để chặn lượt lưu). */
export function findLinesBelowReceived(originals: PurchaseOrderItem[], draft: RepriceDraft): string[] {
  return applyRepriceDraft(originals, draft)
    .filter((item) => item.id && draft[item.id] && isQtyBelowReceived(item))
    .map((item) => item.product_code || item.product_name || `#${item.id}`)
}
