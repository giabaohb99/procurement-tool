/**
 * duoc-CR-784 — luật hiển thị của tab Giá 5 lần gần nhất (bám `renderMatrix` của bản mẫu).
 *
 * Màu đơn giá một lần mua đo với lần mua LIỀN TRƯỚC nó (lần cũ hơn kế bên): cao hơn thì đỏ (mua đắt lên),
 * thấp hơn thì xanh. Lần cuối cùng đang hiện không có lần cũ hơn để so nên không tô.
 */
import type { LastPricesFilters } from '../components/packaging-last-prices-toolbar'
import type {
  PackagingLastPricesParams,
  PackagingLastPurchase,
  PackagingLastPricesRow,
} from '../types/packaging-cost-types'
import { packagingDiffTone } from './packaging-price-format'

/** Các lựa chọn "Số lần hiển thị" (máy chủ nhận 2–10, mặc định 5). */
export const LAST_PRICE_N_OPTIONS = [3, 5, 10] as const
export const LAST_PRICE_DEFAULT_N = 5

/** Chế độ gần nhất: chỉ nạp ngần này mã có lần mua mới nhất (người chủ chốt 26/11/2026), không phân trang. */
export const RECENT_CODES_LIMIT = 20

/**
 * Chế độ gần nhất = chưa chọn "Tất cả", không chọn nhóm và không bộ lọc nào khác (ô chọn mã, nhà cung cấp, ngày, biến động,
 * ngưỡng %, phạm vi định mức, các công tắc). `n` và `showQty` chỉ đổi cột hiện nên không tính.
 */
export function isRecentMode(filters: LastPricesFilters): boolean {
  return (
    !filters.all &&
    filters.groups.length === 0 &&
    filters.codes.length === 0 &&
    filters.suppliers.length === 0 &&
    !filters.from &&
    !filters.to &&
    filters.trend === 'all' &&
    filters.minPct <= 0 &&
    !filters.onlyPriced &&
    !filters.bomOnly &&
    filters.scope === 'all'
  )
}

/** Lần mua thứ `index` (0 = gần nhất); chưa đủ lần thì `null`. */
/** Nhãn nhóm cột của lần `index` (0 = gần nhất) — dùng cho hàng tiêu đề nhóm của bảng. */
export function purchaseGroupLabel(index: number): string {
  return index === 0 ? 'Lần 1 (gần nhất)' : `Lần ${index + 1}`
}

export function purchaseAt(row: PackagingLastPricesRow, index: number): PackagingLastPurchase | null {
  return row.purchases[index] ?? null
}

/**
 * Lớp màu của đơn giá lần `index` so với lần `index + 1` (cũ hơn kế bên). `undefined` = không tô:
 * không có lần cũ hơn, thiếu giá một vế, hoặc bằng nhau.
 */
export function purchaseTrendTone(row: PackagingLastPricesRow, index: number): string | undefined {
  const current = purchaseAt(row, index)?.price
  const older = purchaseAt(row, index + 1)?.price
  if (typeof current !== 'number' || typeof older !== 'number') return undefined
  return packagingDiffTone(current - older)
}

/**
 * Bộ lọc màn hình → tham số gửi máy chủ (danh sách VÀ Xuất Excel dùng chung nên ra cùng thứ tự). Chỉ gửi giá trị đã
 * khác mặc định; `only_priced` luôn gửi tường minh để không lệ thuộc mặc định phía máy chủ.
 * `sort.by` rỗng = thôi xếp, không gửi `sort_by`.
 */
export function buildLastPricesParams(
  filters: LastPricesFilters,
  sort: { by: string; dir: 'asc' | 'desc' },
): PackagingLastPricesParams {
  return {
    n: filters.n,
    code: filters.codes.length ? filters.codes : undefined,
    group: filters.groups.length ? filters.groups : undefined,
    supplier: filters.suppliers.length ? filters.suppliers : undefined,
    date_from: filters.from || undefined,
    date_to: filters.to || undefined,
    trend: filters.trend === 'all' ? undefined : filters.trend,
    min_pct: filters.minPct > 0 ? filters.minPct : undefined,
    only_priced: filters.onlyPriced,
    bom_only: filters.bomOnly || undefined,
    scope: filters.scope,
    ...(sort.by ? { sort_by: sort.by, sort_dir: sort.dir } : {}),
  }
}

/** Khóa xếp theo lần `p{k}_...` vượt quá số lần đang hiện thì không còn cột để xếp → bỏ xếp. */
export function sortKeyOutsideN(sortBy: string, n: number): boolean {
  const slot = /^p(\d+)_/.exec(sortBy)
  return slot !== null && Number(slot[1]) > n
}
