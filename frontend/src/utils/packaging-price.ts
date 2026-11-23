/**
 * duoc-CR-784 — định dạng số + nhãn mã của cụm Giá bao bì (bản v1).
 *
 * Đơn giá hiện bằng `fmtPrice` (đủ 4 số lẻ), thành tiền bằng `fmtVND` — đúng luật `utils/money.ts`.
 * `null` = chưa có giá → chuỗi rỗng; nơi vẽ ô tự đặt gạch "—" (khác với 0 đồng).
 */
import { fmtPrice, fmtVND } from './money'
import type { PackagingSelectedCode, PackagingWarning, PackagingWarningInput } from '../api/packaging-cost-types'

type Num = number | null | undefined

/** Màu chênh lệch (người chủ chốt 20/11/2026): TĂNG xanh, GIẢM đỏ, bằng 0 không tô. */
export const PKG_UP_COLOR = '#16a34a'
export const PKG_DOWN_COLOR = '#dc2626'

export const isNum = (v: Num): v is number => typeof v === 'number' && Number.isFinite(v)

/** Đơn giá / chi phí một đơn vị. */
export const priceText = (v: Num): string => (isNum(v) ? fmtPrice(v) : '')

/** Thành tiền (làm tròn về đồng). */
export const amountText = (v: Num): string => (isNum(v) ? fmtVND(v) : '')

/** Chênh lệch có dấu: "+1.250", "-85,5", "0". */
export function diffText(v: Num): string {
  if (!isNum(v)) return ''
  const t = fmtPrice(v)
  return v > 0 ? `+${t}` : t
}

/** Số lượng (tối đa 3 số lẻ, đúng cột DECIMAL(18,3)). */
export const qtyText = (v: Num): string =>
  isNum(v) ? v.toLocaleString('vi-VN', { maximumFractionDigits: 3 }) : ''

/** Phần trăm có dấu một số lẻ; vào là TỶ SỐ (0.125 → "+12,5%"). */
export function pctText(ratio: Num): string {
  if (!isNum(ratio)) return ''
  const p = ratio * 100
  const t = p.toLocaleString('vi-VN', { minimumFractionDigits: 1, maximumFractionDigits: 1 })
  return p > 0 ? `+${t}%` : `${t}%`
}

/** Màu theo chiều chênh; `undefined` = không tô (bằng 0 hoặc thiếu số). */
export function diffColor(v: Num): string | undefined {
  if (!isNum(v) || Math.abs(v) < 1e-6) return undefined
  return v > 0 ? PKG_UP_COLOR : PKG_DOWN_COLOR
}

/** Giá có ra ngoài ngưỡng sàn / trần không (ngưỡng `null` = không đặt phía đó; 0 vẫn là ngưỡng thật). */
export function isOutsideLimit(price: Num, floor: Num, ceiling: Num): boolean {
  if (!isNum(price)) return false
  return (isNum(floor) && price < floor) || (isNum(ceiling) && price > ceiling)
}

// ── Nhãn mã ─────────────────────────────────────────────────────────────────────
// v1 không có tệp trạng thái sinh tự động: chép lại vài nhãn cần dùng từ
// `backend/app/core/packaging_price_codes.py` (PackagingRole, CostWarning, PriceSourceType, CostTrend).
// Số đã cấp không đổi, không tái dùng nên chép tay an toàn; mã lạ rơi về "Mã n".

export const PACKAGING_ROLE_LABELS: Record<number, string> = {
  1: 'Chai', 2: 'Nắp', 3: 'Nhãn', 4: 'Nhãn thùng', 5: 'Thùng',
}
export const COST_WARNING_KIND = { BELOW_FLOOR: 6, ABOVE_CEILING: 7 } as const
const COST_WARNING_LABELS: Record<number, string> = {
  1: 'Thiếu giá chai', 2: 'Chưa khai mã thành phần', 3: 'Thiếu giá thành phần', 4: 'Thiếu quy cách thùng',
  5: 'ĐVT mua khác ĐVT danh mục', 6: 'Dưới ngưỡng sàn', 7: 'Vượt ngưỡng trần',
}
/** `CostTrend` — xu hướng chi phí của một sản phẩm so với giá cũ. */
export const COST_TREND = { UP: 1, DOWN: 2, SAME: 3, NO_PRICE: 4 } as const
const COST_TREND_LABELS: Record<number, string> = { 1: 'Tăng', 2: 'Giảm', 3: 'Không đổi', 4: 'Chưa có giá' }
export const trendLabel = (trend: number | null | undefined): string =>
  trend == null ? '' : (COST_TREND_LABELS[trend] ?? `Mã ${trend}`)
/** `PriceSourceType.PO_LINE` — dòng ĐMH đang mở (giá còn có thể đổi). */
export const PRICE_SOURCE_PO_LINE = 2

export const roleLabel = (role: number | null | undefined): string =>
  role == null ? '' : (PACKAGING_ROLE_LABELS[role] ?? `Mã ${role}`)

/** Máy chủ có chỗ gửi mã trần, có chỗ gửi `{kind, role}` — quy về một khuôn. */
export const normalizeWarnings = (list: readonly PackagingWarningInput[] | null | undefined): PackagingWarning[] =>
  (list ?? []).map((w) => (typeof w === 'number' ? { kind: w } : w))

/** Một cảnh báo thành chữ; gắn với thành phần thì kèm tên thành phần ("Thiếu giá thành phần: Nắp"). */
export function warningText(w: PackagingWarning): string {
  const kind = COST_WARNING_LABELS[w.kind] ?? `Mã ${w.kind}`
  return w.role ? `${kind}: ${roleLabel(w.role)}` : kind
}

/** Cột Ghi chú: mọi cảnh báo nối bằng "; ", bỏ câu trùng. */
export const joinWarnings = (list: readonly PackagingWarningInput[] | null | undefined): string =>
  [...new Set(normalizeWarnings(list).map(warningText))].join('; ')

/** Câu ghi chú một mã đã chọn: cảnh báo máy chủ gửi + câu ngoài ngưỡng tính tại chỗ (giá giả định chưa kịp gửi, trễ 400 ms). */
export function selectedCodeNote(row: PackagingSelectedCode, applied: number | null): string {
  //  Bỏ cảnh báo ngưỡng của máy chủ rồi tự tính lại theo giá đang gõ: vừa gõ về trong ngưỡng mà ô vẫn báo "vượt trần" thêm một nhịp là sai.
  const limitKinds: number[] = [COST_WARNING_KIND.BELOW_FLOOR, COST_WARNING_KIND.ABOVE_CEILING]
  const notes = [joinWarnings(normalizeWarnings(row.warnings).filter((w) => !limitKinds.includes(w.kind)))]
  if (isNum(applied) && isNum(row.floor) && applied < row.floor) notes.push(warningText({ kind: COST_WARNING_KIND.BELOW_FLOOR }))
  if (isNum(applied) && isNum(row.ceiling) && applied > row.ceiling) notes.push(warningText({ kind: COST_WARNING_KIND.ABOVE_CEILING }))
  return notes.filter(Boolean).join('; ')
}
