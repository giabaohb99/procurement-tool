/**
 * duoc-CR-784 — trạng thái màn hình <-> chuỗi truy vấn của URL cho hai màn Tác động giá và Tổng hợp theo sản phẩm (bản v1),
 * để F5 / gửi link vẫn giữ nguyên mã đã chọn, giá giả định, khoảng ngày, từ khóa, chip lọc, cột xếp và trang. Cùng tên tham số
 * với bản v2: `codes` (mã cách nhau dấu phẩy) · `assumed` (`MÃ:GIÁ` cách nhau dấu phẩy) · `date_from` / `date_to` (YYYY-MM-DD)
 * · `q` · `sort_by` / `sort_dir` · `page` / `page_size` · tên lọc của máy chủ (`trend`, `part_roles`, `carton_qty_min`…).
 *
 * Phần ghi dùng lại bộ dựng của bản in / Xuất Excel (`buildImpactPrintSearch`, `buildOverviewParams`) nên màn, bản in và tệp
 * Excel luôn đọc cùng một bộ lọc. Phần đọc coi URL là dữ liệu từ ngoài vào: khóa xếp ngoài danh sách, ngày sai lịch, mã quá
 * dài / quá trần (500), biên khoảng không đọc được thành số đều bị bỏ, không bao giờ làm màn hỏng.
 */
import type { PackagingOverviewTrend } from '../api/packaging-cost-types'
import {
  EMPTY_IMPACT_FILTERS, impactFiltersToRequest, parseRangeText, rangeTextProblem,
  type ImpactAdvancedFilters, type ImpactRangeKey, type ImpactRangeText,
} from './packaging-impact-filters'
import { buildOverviewParams } from './packaging-overview'
import { buildImpactPrintSearch, parseImpactPrintSearch } from './packaging-print'

export const IMPACT_DEFAULT_PAGE_SIZE = 50
export const OVERVIEW_DEFAULT_PAGE_SIZE = 100
/** Cỡ trang bộ chọn "n/trang" của `Pagination` cho phép; giá trị khác từ URL bị bỏ. */
const PAGE_SIZES = [10, 20, 50, 100]
const TRENDS: readonly string[] = ['all', 'up', 'down', 'flat', 'missing']
const MAX_QUERY_LENGTH = 100

/** Khóa xếp của bảng Tổng hợp theo sản phẩm (cột của `buildProductColumns` + "% chênh"). */
const OVERVIEW_SORT_KEYS = [
  'fg_code', 'fg_name', 'carton_qty', 'cost_old_bottle', 'cost_new_bottle', 'diff_bottle', 'diff_carton', 'pct',
  'part_bottle', 'part_cap', 'part_label', 'part_carton_label', 'part_carton',
]

/** Mọi khóa mà màn Tác động giá sở hữu trên URL (ghi đè / xóa đúng các khóa này, không đụng tham số khác). */
export const IMPACT_URL_KEYS = [
  'codes', 'assumed', 'date_from', 'date_to', 'q', 'sort_by', 'sort_dir', 'page', 'page_size', 'trend', 'part_roles',
  'carton_qty_min', 'carton_qty_max', 'diff_bottle_min', 'diff_bottle_max', 'diff_carton_min', 'diff_carton_max',
  'cost_new_bottle_min', 'cost_new_bottle_max', 'warnings_only',
] as const
/** Mọi khóa mà màn Tổng hợp theo sản phẩm sở hữu trên URL. */
export const OVERVIEW_URL_KEYS = [
  'q', 'trend', 'sort_by', 'sort_dir', 'page', 'page_size', 'part_roles', 'warnings_only',
  'carton_qty_min', 'carton_qty_max', 'cost_old_bottle_min', 'cost_old_bottle_max', 'cost_new_bottle_min', 'cost_new_bottle_max',
  'diff_bottle_min', 'diff_bottle_max', 'diff_carton_min', 'diff_carton_max', 'pct_min', 'pct_max',
] as const

/** Tên khóa máy chủ của từng ô khoảng (`<tên>_min` / `<tên>_max`). */
const RANGE_PARAM: Record<ImpactRangeKey, string> = {
  cartonQty: 'carton_qty', diffBottle: 'diff_bottle', diffCarton: 'diff_carton',
  costNewBottle: 'cost_new_bottle', costOldBottle: 'cost_old_bottle', pct: 'pct',
}

/** Một biên trên URL ("1234.5", số máy) -> chữ kiểu ô nhập (dấu phẩy thập phân); không đọc được -> rỗng. */
function boundText(raw: string | null): string {
  if (raw === null) return ''
  const text = raw.trim().replace('.', ',')
  return parseRangeText(text) == null ? '' : text
}

/** Các khóa lọc nâng cao trên URL -> trạng thái biểu mẫu. Ô khoảng sai luật (Từ > Đến, quy cách không nguyên) bị bỏ cả ô. */
function filtersFromSearch(s: URLSearchParams, trendAllowed: boolean): ImpactAdvancedFilters {
  const f: ImpactAdvancedFilters = { ...EMPTY_IMPACT_FILTERS }
  const trend = s.get('trend')
  if (trendAllowed && trend && trend !== 'all' && TRENDS.includes(trend)) f.trend = trend as PackagingOverviewTrend
  f.roles = [...new Set((s.get('part_roles') ?? '').split(',').map(Number).filter((r) => [1, 2, 3, 4, 5].includes(r)))].sort((a, b) => a - b)
  f.warningsOnly = s.get('warnings_only') === '1' || s.get('warnings_only') === 'true'
  for (const key of Object.keys(RANGE_PARAM) as ImpactRangeKey[]) {
    const range: ImpactRangeText = { min: boundText(s.get(`${RANGE_PARAM[key]}_min`)), max: boundText(s.get(`${RANGE_PARAM[key]}_max`)) }
    f[key] = rangeTextProblem(key, range) ? { min: '', max: '' } : range
  }
  return f
}

function pageFromSearch(s: URLSearchParams, defaultSize: number): { page: number; pageSize: number } {
  const page = Number(s.get('page'))
  const size = Number(s.get('page_size'))
  return {
    page: Number.isInteger(page) && page >= 1 && page <= 100000 ? page : 1,
    pageSize: PAGE_SIZES.includes(size) ? size : defaultSize,
  }
}

const trimQuery = (s: URLSearchParams) => (s.get('q') ?? '').trim().slice(0, MAX_QUERY_LENGTH)

// ── Tác động giá ────────────────────────────────────────────────────────────────

export interface ImpactScreenState {
  codes: string[]
  assumed: Record<string, number>
  range: { from: string; to: string }
  keyword: string
  filters: ImpactAdvancedFilters
  sortBy: string
  sortDir: 'asc' | 'desc'
  page: number
  pageSize: number
}

/** Trạng thái màn Tác động giá -> chuỗi truy vấn (không có "?"). Giá trị mặc định / rỗng không ghi để link gọn. */
export function impactScreenToSearch(st: ImpactScreenState): string {
  const assumed = Object.fromEntries(st.codes.filter((c) => st.assumed[c] != null).map((c) => [c, st.assumed[c]]))
  const s = new URLSearchParams(buildImpactPrintSearch({
    codes: st.codes,
    assumed_prices: Object.keys(assumed).length ? assumed : undefined,
    date_from: st.range.from || undefined,
    date_to: st.range.to || undefined,
    q: st.keyword.trim() || undefined,
    ...impactFiltersToRequest(st.filters),
    ...(st.sortBy ? { sort_by: st.sortBy, sort_dir: st.sortDir } : {}),
  }))
  if (!st.codes.length) s.delete('codes')
  //  Bản in lặp khóa `assumed`; màn hình dùng MỘT khóa cách nhau dấu phẩy (cùng bản v2).
  const pairs = s.getAll('assumed')
  s.delete('assumed')
  if (pairs.length) s.set('assumed', pairs.join(','))
  if (st.page > 1) s.set('page', String(st.page))
  if (st.pageSize !== IMPACT_DEFAULT_PAGE_SIZE) s.set('page_size', String(st.pageSize))
  return s.toString()
}

/** Chuỗi truy vấn -> trạng thái màn Tác động giá (đã kiểm). Link hỏng / rỗng ra đúng trạng thái trống. */
export function searchToImpactScreen(search: string): ImpactScreenState {
  const raw = new URLSearchParams(search)
  //  Chấp nhận cả dạng một khóa cách nhau dấu phẩy lẫn dạng lặp khóa của bản in.
  const norm = new URLSearchParams(raw)
  norm.delete('assumed')
  raw.getAll('assumed').flatMap((v) => v.split(',')).forEach((pair) => norm.append('assumed', pair))
  const req = parseImpactPrintSearch(norm)
  return {
    codes: req.codes,
    assumed: req.assumed_prices ?? {},
    range: { from: req.date_from ?? '', to: req.date_to ?? '' },
    keyword: req.q ?? '',
    filters: filtersFromSearch(norm, true),
    sortBy: req.sort_by ?? '',
    sortDir: req.sort_dir ?? 'asc',
    ...pageFromSearch(norm, IMPACT_DEFAULT_PAGE_SIZE),
  }
}

// ── Tổng hợp theo sản phẩm ──────────────────────────────────────────────────────

export interface OverviewScreenState {
  keyword: string
  trend: PackagingOverviewTrend
  filters: ImpactAdvancedFilters
  sortBy: string
  sortDir: 'asc' | 'desc'
  page: number
  pageSize: number
}

export function overviewScreenToSearch(st: OverviewScreenState): string {
  const params = buildOverviewParams(st.trend, st.keyword, { by: st.sortBy, dir: st.sortDir }, st.filters)
  const s = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => { if (v !== undefined && v !== false) s.set(k, v === true ? '1' : String(v)) })
  if (st.page > 1) s.set('page', String(st.page))
  if (st.pageSize !== OVERVIEW_DEFAULT_PAGE_SIZE) s.set('page_size', String(st.pageSize))
  return s.toString()
}

export function searchToOverviewScreen(search: string): OverviewScreenState {
  const s = new URLSearchParams(search)
  const trend = s.get('trend') ?? 'all'
  const sortBy = s.get('sort_by') ?? ''
  const sorted = OVERVIEW_SORT_KEYS.includes(sortBy)
  return {
    keyword: trimQuery(s),
    trend: (TRENDS.includes(trend) ? trend : 'all') as PackagingOverviewTrend,
    //  Xu hướng của màn Tổng hợp đi bằng chip riêng, không nằm trong hộp lọc nâng cao.
    filters: filtersFromSearch(s, false),
    sortBy: sorted ? sortBy : '',
    sortDir: sorted && s.get('sort_dir') === 'desc' ? 'desc' : 'asc',
    ...pageFromSearch(s, OVERVIEW_DEFAULT_PAGE_SIZE),
  }
}
