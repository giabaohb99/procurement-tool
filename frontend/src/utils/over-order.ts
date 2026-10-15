// bao-CR-619 — cảnh báo đặt vượt khi tạo thêm ĐMH từ YCMH. Dữ liệu lấy từ
// GET /api/purchase-requests/{id}/order-progress: `ordered` = đơn đã duyệt trở đi (nghĩa cũ),
// `pending` = đơn nháp / chờ duyệt / bị trả lại, `orders` = từng đơn còn sống theo mã hàng.

export type OrderRef = {
  id: number
  code: string
  status: string
  status_label: string
  pending: boolean
  qty: number
  received: number
}

export type OrderProgress = {
  ordered: Record<string, number>
  pending: Record<string, number>
  orders: Record<string, OrderRef[]>
}

/** Bản tóm tắt gửi kèm sang form tạo ĐMH (state.fromPr.progress), theo mã hàng. */
export type LineProgress = {
  name: string
  requested: number
  ordered: number
  pending: number
  orders: OrderRef[]
}

export const EMPTY_PROGRESS: OrderProgress = { ordered: {}, pending: {}, orders: {} }

const fmtQty = (n: number) => Number(n || 0).toLocaleString('vi-VN')

/** «đã đặt 80 (PO00358 Đã duyệt, đã nhận 10) · đang chờ duyệt 100 (PO00371 Nháp)» — phần nào bằng 0 thì bỏ. */
export function describeOrdered(lp: Pick<LineProgress, 'ordered' | 'pending' | 'orders'>): string {
  const live = (lp.orders || []).filter((o) => !o.pending)
  const waiting = (lp.orders || []).filter((o) => o.pending)
  const parts: string[] = []
  const list = (rows: OrderRef[], withReceived: boolean) => rows
    .map((o) => `${o.code} ${o.status_label}${withReceived ? `, đã nhận ${fmtQty(o.received)}` : ''}`)
    .join('; ')
  parts.push(`đã đặt ${fmtQty(lp.ordered)}${live.length ? ` (${list(live, true)})` : ''}`)
  if (lp.pending > 0) parts.push(`đang chờ duyệt ${fmtQty(lp.pending)} (${list(waiting, false)})`)
  return parts.join(' · ')
}

/** Dòng ĐMH đang soạn vượt số còn lại của YCMH (yêu cầu − đã đặt − đang chờ duyệt). Trùng mã thì cộng gộp. */
export function overOrderLines(items: { product_code?: string; qty_order?: any }[],
  progress: Record<string, LineProgress> | undefined) {
  if (!progress) return []
  const thisOrder: Record<string, number> = {}
  for (const it of items) {
    const code = (it.product_code || '').trim()
    if (code && progress[code]) thisOrder[code] = (thisOrder[code] || 0) + (Number(it.qty_order) || 0)
  }
  return Object.entries(thisOrder)
    .map(([code, qty]) => {
      const lp = progress[code]
      const total = lp.ordered + lp.pending + qty
      return { code, lp, qty, total, over: total - lp.requested }
    })
    .filter((x) => x.qty > 0 && x.over > 0)
}

export { fmtQty }
