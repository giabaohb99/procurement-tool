/**
 * duoc-CR-784 — luật thuần của cụm Giá bao bì (bản v1): tìm mã kiểu bản mẫu, đường dẫn sâu của Lịch sử mua
 * hàng (`?codes=` / `?fg=`), bộ lọc màn hình → tham số máy chủ và trục biểu đồ
 * (thẻ số liệu ở `packaging-history-summary.ts`).
 */
import type {
  PackagingCodeOption, PackagingHistoryMode, PackagingHistoryParams, PackagingHistoryPoint,
  PackagingLastPricesParams, PackagingLastPricesRow, PackagingLastPurchase,
  LastPricesTrend,
} from '../api/packaging-cost-types'
import { diffColor, roleLabel } from './packaging-price'

/** Trần số mã một lượt tính (`POST /impact` nhận `codes: str[1..500]`). */
export const PACKAGING_MAX_CODES = 500
/** Trần số mã một lượt của Lịch sử mua hàng — khớp `MAX_CODES` của `history_service.py`. */
export const PACKAGING_HISTORY_MAX_CODES = 200

export const PACKAGING_PATHS = {
  impact: '/packaging-cost/impact',
  priceList: '/packaging-cost/price-list',
  lastPrices: '/packaging-cost/last-prices',
  history: '/packaging-cost/history',
  products: '/packaging-cost/products',
  quotes: '/product-price-quotes',
  boms: '/packaging-boms',
} as const

/** Bỏ dấu + hạ chữ thường để tìm không phân biệt dấu ("nắp 0085" ra NAP0085). */
export const fold = (s: string): string =>
  s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/gi, 'd').toLowerCase().trim()

// ── Tìm mã bao bì ───────────────────────────────────────────────────────────────

/** Một cụm chữ ứng với nhóm nào: trùng hẳn tên nhóm trước ("nhan" = Nhãn, không phải Nhãn thùng), rồi chữ đầu của tên nhóm. */
function resolveGroup(term: string, groups: readonly string[]): string | null {
  return groups.find((g) => fold(g) === term) ?? groups.find((g) => fold(g).split(/\s+/)[0] === term) ?? null
}

/**
 * Hàm lọc cho từ khóa `query`. Gõ TÊN NHÓM ("chai", "nắp", "nhãn, thùng") = lọc cả nhóm để bấm "Chọn tất cả" là chọn
 * đúng nhóm đó; còn lại tìm không dấu, mọi từ phải có mặt trong mã / tên / nhóm. Từ khóa rỗng = lấy hết.
 */
export function buildCodeMatcher(query: string, groups: readonly string[]): (o: PackagingCodeOption) => boolean {
  const folded = fold(query)
  if (!folded) return () => true
  const parts = folded.split(',').map((p) => p.trim()).filter(Boolean)
  const matched = parts.map((p) => resolveGroup(p, groups))
  if (matched.length > 0 && matched.every(Boolean)) {
    const wanted = new Set(matched)
    return (o) => wanted.has(o.group)
  }
  const terms = folded.split(/[\s,]+/).filter(Boolean)
  return (o) => {
    const hay = fold(`${o.code} ${o.name} ${o.group}`)
    return terms.every((t) => hay.includes(t))
  }
}

/** Thứ tự bày: chai → nắp → nhãn → nhãn thùng → thùng, nhóm khác sau, cùng nhóm theo mã. */
const GROUP_ORDER = ['chai', 'nap', 'nhan', 'nhan thung', 'thung']
export function sortCodeOptions(options: readonly PackagingCodeOption[]): PackagingCodeOption[] {
  const rank = (g: string) => { const i = GROUP_ORDER.indexOf(fold(g)); return i < 0 ? GROUP_ORDER.length : i }
  return [...options].sort((a, b) => rank(a.group) - rank(b.group) || a.code.localeCompare(b.code))
}

/** Các nhóm có mặt trong danh sách, giữ thứ tự của `sortCodeOptions`. */
export const collectGroups = (options: readonly PackagingCodeOption[]): string[] =>
  [...new Set(sortCodeOptions(options).map((o) => o.group).filter(Boolean))]

/** Nhóm dùng để HIỂU từ khóa: nhóm trong dữ liệu + năm tên vai trò (để "thùng" luôn là nhóm Thùng dù chưa có mã thùng). */
export const collectSearchGroups = (options: readonly PackagingCodeOption[], roleNames: readonly string[]): string[] =>
  [...new Set([...roleNames, ...collectGroups(options)])]

// ── Lịch sử mua hàng: đường dẫn sâu + tham số ──────────────────────────────────

export interface HistorySelection { mode: PackagingHistoryMode; codes: string[]; fg: string[] }
export interface HistoryFilters { q: string; suppliers: string[]; from: string; to: string }
export const EMPTY_HISTORY_FILTERS: HistoryFilters = { q: '', suppliers: [], from: '', to: '' }

function splitCodes(raw: string | null): string[] {
  if (!raw) return []
  const seen = new Set<string>()
  raw.split(',').forEach((p) => { const c = p.trim(); if (c) seen.add(c) })
  return [...seen].slice(0, PACKAGING_HISTORY_MAX_CODES)
}

/** Đọc lựa chọn từ URL. `mode` nói rõ thì theo `mode`; không nói thì chỉ có `fg` là chế độ sản phẩm, còn lại chế độ mã. */
export function parseHistorySearch(search: URLSearchParams): HistorySelection {
  const fg = splitCodes(search.get('fg'))
  const codes = splitCodes(search.get('codes'))
  const explicit = search.get('mode')
  const mode: PackagingHistoryMode = explicit === 'product' || explicit === 'code'
    ? explicit : fg.length > 0 && codes.length === 0 ? 'product' : 'code'
  return { mode, codes, fg }
}

/** Ghi lựa chọn ra chuỗi truy vấn; giữ CẢ HAI danh sách để đổi chế độ qua lại không mất lựa chọn bên kia. */
export function buildHistorySearch(sel: HistorySelection): Record<string, string> {
  const out: Record<string, string> = {}
  if (sel.mode === 'product' || sel.fg.length > 0) out.mode = sel.mode
  if (sel.codes.length) out.codes = sel.codes.join(',')
  if (sel.fg.length) out.fg = sel.fg.join(',')
  return out
}

/** Đường dẫn tới Lịch sử mua hàng của MỘT mã VTBB — dùng cho ô mã ở các bảng khác. */
export const historyHref = (code: string): string =>
  `${PACKAGING_PATHS.history}?${new URLSearchParams({ codes: code }).toString()}`

/** Đường dẫn tới Lịch sử mua hàng của MỘT sản phẩm (chế độ "Theo mã sản phẩm": mọi mã thành phần của định mức). */
export const historyProductHref = (fgCode: string): string =>
  `${PACKAGING_PATHS.history}?${new URLSearchParams({ fg: fgCode }).toString()}`

export function buildHistoryParams(
  sel: HistorySelection, f: HistoryFilters, search: string, sort: { by: string; dir: 'asc' | 'desc' },
): PackagingHistoryParams {
  const isProduct = sel.mode === 'product'
  return {
    mode: sel.mode,
    codes: !isProduct && sel.codes.length ? sel.codes : undefined,
    fg_codes: isProduct && sel.fg.length ? sel.fg : undefined,
    q: search.trim() || undefined,
    supplier: f.suppliers.length ? f.suppliers : undefined,
    date_from: f.from || undefined,
    date_to: f.to || undefined,
    ...(sort.by ? { sort_by: sort.by, sort_dir: sort.dir } : {}),
  }
}

/** "Chai" / "Nắp"... — thành phần của dòng trong định mức sản phẩm (chế độ sản phẩm); chế độ mã không có vai trò thì rỗng. */
export const historyRoleText = (row: { role: number | null }): string => (row.role === null ? '' : roleLabel(row.role))

/** Khóa dòng của bảng: chế độ sản phẩm một dòng sổ giá hiện ở nhiều sản phẩm nên `id` một mình không duy nhất. */
export const historyRowKey = (row: { id: number; fg_code: string }): string => (row.fg_code ? `${row.fg_code}:${row.id}` : String(row.id))

/**
 * Trục giá nới ra hai đầu một đoạn (10% biên độ, tối thiểu 2% giá) — đường giá không dính sát khung, giá đi ngang vẫn có
 * khoảng để vẽ. Trục KHÔNG bắt đầu từ 0: biến động vài phần trăm sẽ dẹp lì nếu kéo về 0.
 */
export function priceAxisDomain(points: readonly PackagingHistoryPoint[]): [number, number] {
  if (points.length === 0) return [0, 1]
  const prices = points.map((p) => p.price)
  const low = Math.min(...prices)
  const high = Math.max(...prices)
  const pad = Math.max((high - low) * 0.1, high * 0.02, 1)
  return [Math.max(0, Math.floor(low - pad)), Math.ceil(high + pad)]
}

// ── Giá mua gần nhất ────────────────────────────────────────────────────────────

export const LAST_PRICE_N_OPTIONS = [3, 5, 10] as const
export const LAST_PRICE_DEFAULT_N = 5

export interface LastPricesFilters {
  q: string
  group: string
  n: number
  scope: 'bom' | 'all'
  suppliers: string[]
  from: string
  to: string
  trend: LastPricesTrend
  minPct: number
  onlyPriced: boolean
  bomOnly: boolean
  showQty: boolean
}

export const EMPTY_LAST_PRICES_FILTERS: LastPricesFilters = {
  q: '', group: '', n: LAST_PRICE_DEFAULT_N, scope: 'bom', suppliers: [], from: '', to: '',
  trend: 'all', minPct: 0, onlyPriced: true, bomOnly: false, showQty: false,
}

/** Nhãn nhóm cột của lần `index` (0 = gần nhất). */
export const purchaseGroupLabel = (index: number): string => (index === 0 ? 'Lần 1 (gần nhất)' : `Lần ${index + 1}`)

export const purchaseAt = (row: PackagingLastPricesRow, index: number): PackagingLastPurchase | null =>
  row.purchases[index] ?? null

/** Màu đơn giá lần `index` đo với lần mua LIỀN TRƯỚC nó (cũ hơn, kế bên): cao hơn xanh, thấp hơn đỏ; lần cuối không so được. */
export function purchaseTone(row: PackagingLastPricesRow, index: number): string | undefined {
  const cur = purchaseAt(row, index)?.price
  const old = purchaseAt(row, index + 1)?.price
  if (typeof cur !== 'number' || typeof old !== 'number') return undefined
  return diffColor(cur - old)
}

/** Bộ lọc màn hình → tham số máy chủ (danh sách VÀ Xuất Excel dùng chung nên ra cùng thứ tự). */
export function buildLastPricesParams(
  f: LastPricesFilters, search: string, sort: { by: string; dir: 'asc' | 'desc' },
): PackagingLastPricesParams {
  return {
    n: f.n,
    q: search.trim() || undefined,
    group: f.group || undefined,
    supplier: f.suppliers.length ? f.suppliers : undefined,
    date_from: f.from || undefined,
    date_to: f.to || undefined,
    trend: f.trend === 'all' ? undefined : f.trend,
    min_pct: f.minPct > 0 ? f.minPct : undefined,
    only_priced: f.onlyPriced,
    bom_only: f.bomOnly || undefined,
    scope: f.scope,
    ...(sort.by ? { sort_by: sort.by, sort_dir: sort.dir } : {}),
  }
}

/** Khóa xếp theo lần `p{k}_...` vượt quá số lần đang hiện thì không còn cột để xếp → bỏ xếp. */
export function sortKeyOutsideN(sortBy: string, n: number): boolean {
  const slot = /^p(\d+)_/.exec(sortBy)
  return slot !== null && Number(slot[1]) > n
}

// ── Xếp cột ─────────────────────────────────────────────────────────────────────

/** Cột số (tiền, số lần, ngày) bấm lần đầu ra GIẢM dần — người xem muốn "lớn nhất / mới nhất trước". */
const DESC_FIRST = /(price|date|count|usage|amount|qty|diff|v12|v1n|avg|^max$|^pct$|^new$|^old$)/

/** Bấm tiêu đề cột: cùng cột thì đảo chiều, cột mới thì chiều đầu theo kiểu cột. */
export function nextSort(sortBy: string, sortDir: 'asc' | 'desc', key: string): { by: string; dir: 'asc' | 'desc' } {
  if (sortBy === key) return { by: key, dir: sortDir === 'asc' ? 'desc' : 'asc' }
  return { by: key, dir: DESC_FIRST.test(key) ? 'desc' : 'asc' }
}
