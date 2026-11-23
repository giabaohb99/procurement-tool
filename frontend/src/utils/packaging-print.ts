/**
 * duoc-CR-784 — luật thuần của các BẢN IN cụm Giá bao bì (bản v1): Lịch sử mua hàng và Tác động giá. Bộ lọc màn hình <->
 * chuỗi truy vấn của trang in, câu mô tả bộ lọc, trần số dòng. Cùng luật với bản v2 (`packaging-history-print.ts`,
 * `packaging-impact-print.ts`).
 *
 * Bảng trên màn hình phân trang tại máy chủ nên in màn hình chỉ ra một trang: trang in nhận ĐÚNG bộ lọc (không kèm `page`)
 * qua URL rồi tự nạp đủ mọi dòng. URL là dữ liệu từ ngoài vào (gõ tay, dán link) nên mọi trường được kiểm ở đây trước khi
 * gửi máy chủ: chế độ lạ về `code`, ngày sai khuôn / không có trên lịch bị bỏ, khóa xếp ngoài danh sách bị bỏ, mã cắt ở trần.
 */
import type {
  PackagingHistoryParams, PackagingImpactKpis, PackagingImpactRequest, PackagingMaxIncreaseProduct, PackagingSupplierOption,
} from '../api/packaging-cost-types'
import { fmtDateStr } from './datetime'
import { appendImpactFilterSearch, describeImpactAdvancedFilters, parseImpactFilterSearch } from './packaging-impact-filters'
import { diffText, priceText } from './packaging-price'
import { PACKAGING_HISTORY_MAX_CODES, PACKAGING_MAX_CODES } from './packaging-query'

export const PACKAGING_PRINT_PATHS = {
  history: '/print/packaging-history',
  impact: '/print/packaging-impact',
} as const

/** Cỡ một lượt nạp = trần `MAX_PAGE_SIZE` (500) của máy chủ, để ít vòng nhất. */
export const PRINT_PAGE_SIZE = 500
/** Trần số dòng một bản in: quá thì cắt và báo rõ trên tờ giấy (in cả chục nghìn dòng là treo trình duyệt). */
export const PRINT_ROW_CAP = 5000
/** Khớp `max_length=100` của máy chủ ở ô từ khóa (dài hơn là 422). */
const MAX_QUERY_LENGTH = 100
/** Mã dài hơn thì máy chủ trả 422 (`Str50`) — bỏ ngay từ URL. */
const MAX_CODE_LENGTH = 50

/** Khóa xếp của Lịch sử mua hàng — khớp `SORT_KEYS` của `history_service.py`. */
const HISTORY_SORT_KEYS = ['date', 'code', 'name', 'supplier', 'qty', 'price', 'amount', 'vat', 'source']
/** Khóa xếp bảng sản phẩm của Tác động — khớp `SORT_GETTERS` của `impact_service.py`. */
const IMPACT_SORT_KEYS = [
  'hh_code', 'hh_name', 'carton_qty', 'cost_old_bottle', 'cost_applied_bottle', 'diff_bottle', 'diff_carton',
  'cost_old_carton', 'cost_applied_carton', 'pct', 'trend',
  //  Năm cột thành phần: xếp theo giá đang áp của thành phần (hòa theo mã thành phần rồi mã HH).
  'part_bottle', 'part_cap', 'part_label', 'part_carton_label', 'part_carton',
]

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/

/** Ngày đúng khuôn VÀ có trên lịch (`Date.parse` nuốt cả 30/02 nên dựng lại rồi so chuỗi). */
function validDate(raw: string | null): string | undefined {
  if (!raw || !ISO_DATE.test(raw)) return undefined
  const t = Date.parse(`${raw}T00:00:00Z`)
  return Number.isNaN(t) || new Date(t).toISOString().slice(0, 10) !== raw ? undefined : raw
}

function splitList(raw: string | null, cap: number): string[] {
  if (!raw) return []
  const seen = new Set<string>()
  raw.split(',').forEach((p) => { const c = p.trim(); if (c && c.length <= MAX_CODE_LENGTH) seen.add(c) })
  return [...seen].slice(0, cap)
}

function describeDateRange(from?: string, to?: string): string {
  if (from && to) return `${fmtDateStr(from)} – ${fmtDateStr(to)}`
  if (from) return `từ ${fmtDateStr(from)}`
  if (to) return `đến ${fmtDateStr(to)}`
  return ''
}

/** Số dòng sẽ in và có bị cắt ở trần không — `total` là tổng của máy chủ cho bộ lọc này (hỏng / âm / NaN coi là 0). */
export function planPrintRows(total: number): { rows: number; capped: boolean } {
  const safe = Number.isFinite(total) && total > 0 ? Math.floor(total) : 0
  return { rows: Math.min(safe, PRINT_ROW_CAP), capped: safe > PRINT_ROW_CAP }
}

/** Câu báo khi bản in bị cắt: nói rõ in bao nhiêu trên tổng bao nhiêu và cách thu hẹp. */
export const cappedPrintNotice = (total: number, unit: string): string =>
  `Bộ lọc có ${total.toLocaleString('vi-VN')} ${unit} — bản in chỉ gồm ${PRINT_ROW_CAP.toLocaleString('vi-VN')} dòng đầu. Thu hẹp bộ lọc rồi in lại để có đủ.`

// ── Lịch sử mua hàng ────────────────────────────────────────────────────────────

/** Bộ lọc màn hình (không kèm trang) -> chuỗi truy vấn của trang in. Nhà cung cấp lặp khóa (mã có thể chứa dấu phẩy). */
export function buildHistoryPrintSearch(p: PackagingHistoryParams): string {
  const s = new URLSearchParams()
  s.set('mode', p.mode)
  if (p.codes?.length) s.set('codes', p.codes.join(','))
  if (p.hh_codes?.length) s.set('hh_codes', p.hh_codes.join(','))
  if (p.q) s.set('q', p.q)
  ;(p.supplier ?? []).forEach((c) => s.append('supplier', c))
  if (p.date_from) s.set('date_from', p.date_from)
  if (p.date_to) s.set('date_to', p.date_to)
  if (p.sort_by) { s.set('sort_by', p.sort_by); s.set('sort_dir', p.sort_dir ?? 'desc') }
  return s.toString()
}

export const historyPrintHref = (p: PackagingHistoryParams): string =>
  `${PACKAGING_PRINT_PATHS.history}?${buildHistoryPrintSearch(p)}`

/** Chuỗi truy vấn -> tham số `GET /history`. Chỉ giữ mã của chế độ đang bật, giống `buildHistoryParams`. */
export function parseHistoryPrintSearch(s: URLSearchParams): PackagingHistoryParams {
  const mode = s.get('mode') === 'product' ? 'product' : 'code'
  const codes = splitList(s.get('codes'), PACKAGING_HISTORY_MAX_CODES)
  const hh = splitList(s.get('hh_codes'), PACKAGING_HISTORY_MAX_CODES)
  const q = (s.get('q') ?? '').trim().slice(0, MAX_QUERY_LENGTH)
  const suppliers = [...new Set(s.getAll('supplier').map((v) => v.trim()).filter(Boolean))].slice(0, PACKAGING_HISTORY_MAX_CODES)
  const sortBy = s.get('sort_by')
  const sorted = sortBy !== null && HISTORY_SORT_KEYS.includes(sortBy)
  return {
    mode,
    codes: mode === 'code' && codes.length ? codes : undefined,
    hh_codes: mode === 'product' && hh.length ? hh : undefined,
    q: q || undefined,
    supplier: suppliers.length ? suppliers : undefined,
    date_from: validDate(s.get('date_from')),
    date_to: validDate(s.get('date_to')),
    ...(sorted ? { sort_by: sortBy, sort_dir: s.get('sort_dir') === 'asc' ? 'asc' as const : 'desc' as const } : {}),
  }
}

/**
 * Các mảnh của dòng mô tả bộ lọc trên bản in — CHỈ các điều kiện đang bật ngoài lựa chọn mã (chế độ + mã đã có ô chip riêng ở
 * đầu trang): nhà cung cấp (tra tên trong `suppliers` máy chủ trả kèm, không thấy thì in chính mã), khoảng ngày, từ khóa.
 */
export function describeHistoryFilters(p: PackagingHistoryParams, suppliers: readonly PackagingSupplierOption[] = []): string[] {
  const parts: string[] = []
  if (p.supplier?.length) {
    const names = new Map(suppliers.map((x) => [x.code, x.name || x.code]))
    parts.push(`NCC: ${p.supplier.map((c) => names.get(c) ?? c).join(', ')}`)
  }
  const range = describeDateRange(p.date_from, p.date_to)
  if (range) parts.push(`Ngày mua: ${range}`)
  if (p.q) parts.push(`Từ khóa: "${p.q}"`)
  return parts
}

// ── Tác động giá ────────────────────────────────────────────────────────────────

/** Thân tính (chưa kèm trang) -> chuỗi truy vấn. Giá giả định đi bằng các khóa `assumed=MÃ:GIÁ` lặp lại. */
export function buildImpactPrintSearch(r: PackagingImpactRequest): string {
  const s = new URLSearchParams()
  s.set('codes', r.codes.join(','))
  Object.entries(r.assumed_prices ?? {}).forEach(([code, price]) => s.append('assumed', `${code}:${price}`))
  if (r.date_from) s.set('date_from', r.date_from)
  if (r.date_to) s.set('date_to', r.date_to)
  if (r.q) s.set('q', r.q)
  if (r.sort_by) { s.set('sort_by', r.sort_by); s.set('sort_dir', r.sort_dir ?? 'asc') }
  appendImpactFilterSearch(s, r)
  return s.toString()
}

export const impactPrintHref = (r: PackagingImpactRequest): string =>
  `${PACKAGING_PRINT_PATHS.impact}?${buildImpactPrintSearch(r)}`

/**
 * Chuỗi truy vấn -> thân `POST /impact`. `codes` rỗng = link hỏng (trang in báo "chưa chọn mã", không gọi máy chủ). Giá
 * giả định tách ở dấu hai chấm CUỐI (mã có thể chứa dấu hai chấm), chỉ nhận cho mã đang chọn, số hữu hạn và > 0.
 */
export function parseImpactPrintSearch(s: URLSearchParams): PackagingImpactRequest {
  const codes = splitList(s.get('codes'), PACKAGING_MAX_CODES)
  const picked = new Set(codes)
  const assumed: Record<string, number> = {}
  for (const pair of s.getAll('assumed')) {
    const cut = pair.lastIndexOf(':')
    if (cut <= 0) continue
    const code = pair.slice(0, cut).trim()
    const price = Number(pair.slice(cut + 1))
    if (picked.has(code) && Number.isFinite(price) && price > 0) assumed[code] = price
  }
  const q = (s.get('q') ?? '').trim().slice(0, MAX_QUERY_LENGTH)
  const sortBy = s.get('sort_by')
  const sorted = sortBy !== null && IMPACT_SORT_KEYS.includes(sortBy)
  return {
    codes,
    assumed_prices: Object.keys(assumed).length ? assumed : undefined,
    date_from: validDate(s.get('date_from')),
    date_to: validDate(s.get('date_to')),
    q: q || undefined,
    ...parseImpactFilterSearch(s),
    ...(sorted ? { sort_by: sortBy, sort_dir: s.get('sort_dir') === 'desc' ? 'desc' as const : 'asc' as const } : {}),
  }
}

/** Các mảnh của dòng mô tả bộ lọc — CHỈ điều kiện ngoài danh sách mã (mã đã chọn có ô chip riêng): giá giả định, khoảng ngày tính min–max, từ khóa. */
export function describeImpactFilters(r: PackagingImpactRequest): string[] {
  const parts: string[] = []
  const assumed = Object.entries(r.assumed_prices ?? {})
  if (assumed.length) parts.push(`Giá giả định: ${assumed.map(([c, p]) => `${c} = ${priceText(p)}`).join(', ')}`)
  const range = describeDateRange(r.date_from, r.date_to)
  if (range) parts.push(`Khoảng ngày tính min – max: ${range}`)
  if (r.q) parts.push(`Tìm sản phẩm: "${r.q}"`)
  parts.push(...describeImpactAdvancedFilters(r))
  return parts
}

/** "2 chai · 1 nắp" — số mã đã chọn theo nhóm. */
export const describeSelectedGroups = (by: Record<string, number> | undefined): string =>
  Object.entries(by ?? {}).map(([g, n]) => `${n} ${g.toLowerCase()}`).join(' · ')

/** Phần trong ngoặc của dòng tóm tắt: "2 chai · 1 nắp · 1 mã giả định" (rỗng nếu không có gì). */
export const describeImpactSummaryDetail = (k: PackagingImpactKpis): string =>
  [describeSelectedGroups(k.selected_by_group), k.assumed_count ? `${k.assumed_count} mã giả định` : ''].filter(Boolean).join(' · ')

/** Ba thẻ số liệu của màn Tác động — dùng chung cho màn hình và bản in (người chủ chốt 23/11/2026: thẻ, không phải dòng chữ). */
export type ImpactSummaryCardKey = 'selected' | 'affected' | 'top-increase'

export interface ImpactSummaryCard {
  key: ImpactSummaryCardKey
  label: string
  value: string
  /** Đơn vị nhỏ cạnh số to ("VNĐ/thùng"); rỗng nếu không có. */
  unit: string
  /** Dòng phụ thứ nhất ("2 chai · 1 nắp", "Đang lọc: x / M", "+250 /chai"); rỗng nếu không có gì để nói. */
  sub: string
  /** Dòng phụ thứ hai — chỉ thẻ "Tăng nhiều nhất": "HHxxxx — tên sản phẩm". */
  detail: string
  /** Thẻ "Tăng nhiều nhất" có sản phẩm: số tô xanh (chi phí tăng = xanh, luật màu của hệ). */
  tone: 'up' | undefined
  /** Sản phẩm của thẻ "Tăng nhiều nhất" (để bấm vào xem); `null` ở hai thẻ kia và khi không sản phẩm nào tăng. */
  product: PackagingMaxIncreaseProduct | null
}

export const IMPACT_TOP_INCREASE_EMPTY = 'Không có sản phẩm tăng'

/**
 * Dựng ba thẻ từ `kpis`. `filteredTotal` = số sản phẩm sau từ khóa / lọc nâng cao, chỉ truyền khi ĐANG lọc (thẻ "Sản phẩm bị
 * ảnh hưởng" nói rõ "Đang lọc: x / M"; M luôn là số chưa lọc). Thẻ "Tăng nhiều nhất" lấy từ `kpis.max_increase_product`
 * (null → câu "Không có sản phẩm tăng", KHÔNG đưa số âm / 0 ra làm "tăng nhiều nhất").
 */
export function buildImpactSummaryCards(kpis: PackagingImpactKpis, filteredTotal?: number): ImpactSummaryCard[] {
  const top = kpis.max_increase_product ?? null
  const n = (v: number) => v.toLocaleString('vi-VN')
  return [
    { key: 'selected', label: 'Mã đã chọn', value: n(kpis.selected_count), unit: '', sub: describeImpactSummaryDetail(kpis),
      detail: '', tone: undefined, product: null },
    { key: 'affected', label: 'Sản phẩm bị ảnh hưởng', value: n(kpis.affected_products), unit: '',
      sub: filteredTotal == null ? 'Dùng ít nhất 1 mã đã chọn' : `Đang lọc: ${n(filteredTotal)} / ${n(kpis.affected_products)}`,
      detail: '', tone: undefined, product: null },
    { key: 'top-increase', label: 'Tăng nhiều nhất /thùng', value: top ? diffText(top.diff_carton) : IMPACT_TOP_INCREASE_EMPTY,
      unit: top ? 'VNĐ/thùng' : '', sub: top && top.diff_bottle != null ? `${diffText(top.diff_bottle)} /chai` : '',
      detail: top ? `${top.hh_code} — ${top.hh_name}` : '', tone: top ? 'up' : undefined, product: top },
  ]
}
