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
//  Tăng đỏ (giá lên là xấu), giảm xanh — người chủ chốt 27/11/2026, đảo lại quyết định 20/11/2026.
export const PKG_UP_COLOR = '#dc2626'
export const PKG_DOWN_COLOR = '#16a34a'

export const isNum = (v: Num): v is number => typeof v === 'number' && Number.isFinite(v)

/** Đơn giá / chi phí một đơn vị. */
export const priceText = (v: Num): string => (isNum(v) ? fmtPrice(v) : '')

/** Giá TRUNG BÌNH (Giá TB n lần, BQ gia quyền): tối đa 2 số lẻ như bản v2 — trung bình chia ra nhiều chữ số lẻ vô nghĩa. */
export const avgPriceText = (v: Num): string =>
  isNum(v) ? v.toLocaleString('vi-VN', { maximumFractionDigits: 2 }) : ''

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

// ── Nhãn mã ─────────────────────────────────────────────────────────────────────
// v1 không có tệp trạng thái sinh tự động: chép lại vài nhãn cần dùng từ
// `backend/app/core/packaging_price_codes.py` (PackagingRole, CostWarning, PriceSourceType, CostTrend).
// Số đã cấp không đổi, không tái dùng nên chép tay an toàn; mã lạ rơi về "Mã n".

export const PACKAGING_ROLE_LABELS: Record<number, string> = {
  1: 'Chai', 2: 'Nắp', 3: 'Nhãn', 4: 'Nhãn thùng', 5: 'Thùng',
}
/** `QuoteSourceType` — nguồn báo giá VTBB (số 3 để dành cho YCBG). Cùng chữ với `frontend-v2` (`packaging-quote-source.ts`). */
export const QUOTE_SOURCE_LABELS: Record<number, string> = { 1: 'Nhập tay', 2: 'Nhập Excel' }
export const QUOTE_SOURCE_EXCEL = 2

/** Chữ cột "Nguồn" của Báo giá VTBB: "Nhập tay" / "Nhập Excel (lô #N)". */
export function quoteSourceText(type: number | null | undefined, id: number | null | undefined): string {
  if (type == null) return ''
  const label = QUOTE_SOURCE_LABELS[type] ?? `Mã ${type}`
  return type === QUOTE_SOURCE_EXCEL && id != null && id > 0 ? `${label} (lô #${id})` : label
}

//  Số 6 (dưới ngưỡng sàn) và 7 (vượt ngưỡng trần) ĐÃ BỎ cùng bảng ngưỡng (phase 04) — số đã cấp, KHÔNG tái dùng.
const COST_WARNING_LABELS: Record<number, string> = {
  1: 'Thiếu giá chai', 2: 'Chưa khai mã thành phần', 3: 'Thiếu giá thành phần', 4: 'Thiếu quy cách thùng',
  5: 'ĐVT mua khác ĐVT danh mục',
}
/** `CostTrend` — xu hướng chi phí của một sản phẩm so với giá cũ. */
export const COST_TREND = { UP: 1, DOWN: 2, SAME: 3, NO_PRICE: 4 } as const
const COST_TREND_LABELS: Record<number, string> = { 1: 'Tăng', 2: 'Giảm', 3: 'Không đổi', 4: 'Chưa có giá' }
export const trendLabel = (trend: number | null | undefined): string =>
  trend == null ? '' : (COST_TREND_LABELS[trend] ?? `Mã ${trend}`)

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
