/**
 * bao-CR-619 — cảnh báo đặt vượt khi tạo thêm ĐMH từ YCMH (cùng luật bản `frontend/`).
 *
 * Dữ liệu từ `GET /api/purchase-requests/{id}/order-progress`:
 * - `ordered`: đơn đã duyệt trở đi (nghĩa cũ — prefill "còn thiếu");
 * - `pending`: đơn nháp / chờ duyệt / bị trả lại — chưa tính là đã đặt nhưng đã giữ số lượng;
 * - `orders`: từng đơn còn sống theo mã hàng (mã đơn, trạng thái, SL đặt, SL đã nhận).
 */

export interface OrderRef {
  id: number
  code: string
  status: string
  status_label: string
  pending: boolean
  qty: number
  received: number
}

export interface OrderProgress {
  ordered: Record<string, number>
  pending?: Record<string, number>
  orders?: Record<string, OrderRef[]>
}

/** Tình hình đặt của một mã hàng — gửi kèm sang form tạo ĐMH để nhắc đặt vượt. */
export interface LineProgress {
  name: string
  requested: number
  ordered: number
  pending: number
  orders: OrderRef[]
}

export interface OverOrderLine {
  code: string
  progress: LineProgress
  /** Tổng SL đặt của mã này trên đơn đang soạn (trùng mã thì cộng gộp). */
  qty: number
  /** Phần vượt so với số yêu cầu = đã đặt + đang chờ duyệt + đơn này − yêu cầu. */
  over: number
}

export const formatQty = (value: number) => Number(value || 0).toLocaleString('vi-VN')

/** "đã đặt 80 (PO00358 Đã duyệt, đã nhận 10) · đang chờ duyệt 100 (PO00371 Nháp)". */
export function describeOrdered(progress: Pick<LineProgress, 'ordered' | 'pending' | 'orders'>): string {
  const live = progress.orders.filter((order) => !order.pending)
  const waiting = progress.orders.filter((order) => order.pending)
  const list = (rows: OrderRef[], withReceived: boolean) =>
    rows
      .map(
        (order) =>
          `${order.code} ${order.status_label}${withReceived ? `, đã nhận ${formatQty(order.received)}` : ''}`,
      )
      .join('; ')
  const parts = [`đã đặt ${formatQty(progress.ordered)}${live.length ? ` (${list(live, true)})` : ''}`]
  if (progress.pending > 0) {
    parts.push(`đang chờ duyệt ${formatQty(progress.pending)} (${list(waiting, false)})`)
  }
  return parts.join(' · ')
}

/** Dòng hàng của đơn đang soạn làm tổng đặt vượt số yêu cầu của YCMH. */
export function findOverOrders(
  items: { product_code?: string; qty_order?: number | string | null }[],
  progressByCode: Record<string, LineProgress> | undefined,
): OverOrderLine[] {
  if (!progressByCode) return []
  const thisOrder: Record<string, number> = {}
  for (const item of items) {
    const code = (item.product_code || '').trim()
    if (code && progressByCode[code]) {
      thisOrder[code] = (thisOrder[code] || 0) + (Number(item.qty_order) || 0)
    }
  }
  return Object.entries(thisOrder)
    .map(([code, qty]) => {
      const progress = progressByCode[code]
      return { code, progress, qty, over: progress.ordered + progress.pending + qty - progress.requested }
    })
    .filter((line) => line.qty > 0 && line.over > 0)
}
