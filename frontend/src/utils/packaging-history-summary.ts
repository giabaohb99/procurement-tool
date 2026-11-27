/**
 * duoc-CR-784 — các thẻ số liệu của Lịch sử mua hàng (bản v1), chép đúng bộ thẻ của bản mẫu HTML (người chủ chốt
 * 23/11/2026). Cùng luật với bản v2 (`frontend-v2/.../utils/packaging-history-summary-items.ts`):
 *
 * - Đúng MỘT mã: Tổng số lần mua · Tổng số lượng mua · Tổng giá trị mua · Giá thấp nhất – cao nhất · Gần nhất so với lần
 *   đầu · Số nhà cung cấp.
 * - Nhiều mã / mọi mã: Số mã đã chọn (hoặc Số mã hàng) · Tổng số lần mua · Tổng giá trị mua · Số nhà cung cấp.
 * - Theo mã sản phẩm: Số sản phẩm · Mã vật tư liên quan · Số dòng lịch sử · Số nhà cung cấp.
 *
 * Màn hình và bản in dùng chung hàm này. Số tính trên TOÀN BỘ tập đã lọc, không phải trang đang xem.
 */
import type { PackagingHistoryMode, PackagingHistoryStats } from '../api/packaging-cost-types'
import { fmtDateStr } from './datetime'
import { fmtVND } from './money'
import { avgPriceText, pctText, priceText, qtyText } from './packaging-price'

export interface HistorySummaryItem {
  label: string
  value: string
  /** Dòng phụ dưới số (khoảng ngày, ĐVT, số lần có giá...). */
  sub?: string
  /** Chiều giá của thẻ "Gần nhất so với lần đầu": tăng = đỏ, giảm = xanh (luật màu chung của cụm). */
  tone?: 'up' | 'down'
}

export interface HistorySummaryContext {
  singleCode: boolean
  mode: PackagingHistoryMode
  /** Số mã VTBB (chế độ mã) hoặc mã sản phẩm (chế độ sản phẩm) đã chọn; 0 = tất cả. */
  selectedCount: number
}

const DASH = '—'
const countText = (n: number): string => n.toLocaleString('vi-VN')

function dateSpan(s: PackagingHistoryStats): string {
  if (!s.first_date || !s.last_date) return ''
  if (s.first_date === s.last_date) return fmtDateStr(s.first_date)
  return `${fmtDateStr(s.first_date)} → ${fmtDateStr(s.last_date)}`
}

/** Tỷ lệ giá gần nhất / giá lần đầu − 1; thiếu một đầu hoặc giá đầu bằng 0 thì không có số. */
function latestVsFirst(s: PackagingHistoryStats): number | null {
  if (s.first_price == null || s.last_price == null || s.first_price <= 0) return null
  return s.last_price / s.first_price - 1
}

const purchaseCount = (s: PackagingHistoryStats, label: string): HistorySummaryItem =>
  ({ label, value: countText(s.purchase_count), sub: dateSpan(s) })

const amount = (s: PackagingHistoryStats): HistorySummaryItem => ({
  label: 'Tổng giá trị mua',
  value: fmtVND(s.amount_total ?? 0),
  sub: `${countText(s.priced_count)}/${countText(s.purchase_count)} lần có giá`,
})

const suppliers = (s: PackagingHistoryStats): HistorySummaryItem =>
  ({ label: 'Số nhà cung cấp', value: countText(s.supplier_count) })

function singleCodeItems(s: PackagingHistoryStats): HistorySummaryItem[] {
  const ratio = latestVsFirst(s)
  const low = priceText(s.min)
  const high = priceText(s.max)
  const avg = avgPriceText(s.weighted_avg)
  return [
    purchaseCount(s, 'Tổng số lần mua'),
    { label: 'Tổng số lượng mua', value: qtyText(s.qty_total) || '0', sub: s.unit || undefined },
    amount(s),
    { label: 'Giá thấp nhất – cao nhất', value: low && high ? `${low} – ${high}` : DASH, sub: avg ? `BQ gia quyền ${avg}` : undefined },
    {
      label: 'Gần nhất so với lần đầu',
      value: ratio === null ? DASH : pctText(ratio),
      sub: s.first_price != null && s.last_price != null ? `${priceText(s.first_price)} → ${priceText(s.last_price)}` : undefined,
      tone: ratio === null || Math.abs(ratio) < 1e-9 ? undefined : ratio > 0 ? 'up' : 'down',
    },
    suppliers(s),
  ]
}

export function buildHistorySummary(s: PackagingHistoryStats, ctx: HistorySummaryContext): HistorySummaryItem[] {
  if (ctx.singleCode) return singleCodeItems(s)
  const codes = s.code_count ?? 0
  if (ctx.mode === 'product') {
    return [
      //  Số sản phẩm có định mức trong phạm vi chọn (máy chủ đếm); "đã chọn" / "tất cả" như bản mẫu.
      { label: 'Số sản phẩm', value: countText(s.product_count ?? ctx.selectedCount), sub: ctx.selectedCount > 0 ? 'đã chọn' : 'tất cả' },
      { label: 'Mã vật tư liên quan', value: countText(codes), sub: 'chai, nắp, nhãn, nhãn thùng, thùng' },
      purchaseCount(s, 'Số dòng lịch sử'),
      suppliers(s),
    ]
  }
  return [
    ctx.selectedCount > 0
      ? { label: 'Số mã đã chọn', value: countText(ctx.selectedCount), sub: `${countText(codes)} mã có lịch sử mua` }
      : { label: 'Số mã hàng', value: countText(codes), sub: 'tất cả mã có lịch sử mua' },
    purchaseCount(s, 'Tổng số lần mua'),
    amount(s),
    suppliers(s),
  ]
}
