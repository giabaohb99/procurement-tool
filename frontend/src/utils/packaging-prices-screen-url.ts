/**
 * duoc-CR-784 — trạng thái màn hình <-> chuỗi truy vấn của URL cho hai màn Bảng giá VTBB và Giá mua gần nhất (bản v1),
 * để F5 / gửi link vẫn giữ từ khóa, chip nhóm, phạm vi, khoảng ngày, nhà cung cấp, cột xếp và trang. Tên tham số trùng tên
 * tham số API của hai màn (và bản v2): `q` · `group` (Giá mua gần nhất: lặp khóa như `supplier`, bật nhiều chip nhóm; link cũ
 * chỉ một `group=` vẫn đọc được) · `scope` · `only_priced` · `date_from` / `date_to` · `supplier`
 * (lặp khóa như API: `supplier=a&supplier=b`) · `n` (3 / 5 / 10) · `show_qty` · `trend` · `min_pct` · `bom_only` · `sort_by` / `sort_dir` ·
 * `page` / `page_size`. Giá trị mặc định không ghi để link gọn. Mặc định của Giá mua gần nhất (người chủ chốt 26/11/2026):
 * mọi bộ lọc tắt (`scope=all`, `only_priced` tắt), xếp Lần 1 ngày mua giảm dần, 20 dòng / trang — nên chỉ ghi `scope=bom` khi
 * chọn phạm vi định mức và `only_priced=1` khi bật; còn nhận `only_priced=0` của link cũ. Bảng giá VTBB giữ mặc định cũ.
 *
 * Phần đọc coi URL là dữ liệu từ ngoài vào: khóa xếp ngoài danh sách, ngày sai lịch, n ngoài {3,5,10}, cỡ trang lạ, số quá
 * trần đều bị bỏ về mặc định, không bao giờ làm màn hỏng.
 */
import {
  EMPTY_LAST_PRICES_FILTERS, LAST_PRICES_DEFAULT_PAGE_SIZE, LAST_PRICES_DEFAULT_SORT, LAST_PRICE_N_OPTIONS,
  type LastPricesFilters,
} from './packaging-query'
import type { LastPricesTrend } from '../api/packaging-cost-types'

export const PRICES_DEFAULT_PAGE_SIZE = 50
const PAGE_SIZES = [10, 20, 50, 100]
const MAX_QUERY_LENGTH = 100
const MAX_CODE_LENGTH = 50
const MAX_SUPPLIERS = 100
/** Bằng trần `PACKAGING_MAX_CODES` của ô chọn mã và `MAX_CODES` của API. */
const MAX_CODES = 500
const MAX_GROUPS = 200
const TRENDS: readonly LastPricesTrend[] = ['up', 'down', 'flat']
const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/

/** Khóa xếp của bảng Bảng giá VTBB (cột `sort` của `PackagingPriceList`). */
const PRICE_LIST_SORT_KEYS = [
  'code', 'name', 'group', 'purchase_count', 'last_date', 'last_purchase_price', 'prev_purchase_price', 'quote_price',
  'old', 'new', 'diff', 'pct', 'min', 'max', 'usage',
]
/** Khóa xếp cố định của Giá mua gần nhất; các khóa theo lần `p{k}_date` / `p{k}_price` kiểm riêng theo n. */
const LAST_PRICES_SORT_KEYS = ['code', 'name', 'group', 'purchase_count', 'v12', 'v1n', 'avg']

export const PRICE_LIST_URL_KEYS = ['q', 'group', 'scope', 'date_from', 'date_to', 'sort_by', 'sort_dir', 'page', 'page_size'] as const
export const LAST_PRICES_URL_KEYS = [
  'code', 'q', 'group', 'all', 'scope', 'only_priced', 'date_from', 'date_to', 'supplier', 'n', 'show_qty', 'trend', 'min_pct', 'bom_only',
  'sort_by', 'sort_dir', 'page', 'page_size',
] as const

/** Ngày đúng khuôn VÀ có trên lịch (`Date.parse` nuốt cả 30/02 nên dựng lại rồi so chuỗi). */
function validDate(raw: string | null): string {
  if (!raw || !ISO_DATE.test(raw)) return ''
  const t = Date.parse(`${raw}T00:00:00Z`)
  return Number.isNaN(t) || new Date(t).toISOString().slice(0, 10) !== raw ? '' : raw
}

/** Khoảng ngày đọc từ URL; Từ > Đến thì bỏ cả khoảng. */
function rangeFromSearch(s: URLSearchParams): { from: string; to: string } {
  const from = validDate(s.get('date_from'))
  const to = validDate(s.get('date_to'))
  return from && to && from > to ? { from: '', to: '' } : { from, to }
}

const textFromSearch = (s: URLSearchParams, key: string, max = MAX_QUERY_LENGTH): string => (s.get(key) ?? '').trim().slice(0, max)

function pageFromSearch(s: URLSearchParams, defaultPageSize = PRICES_DEFAULT_PAGE_SIZE): { page: number; pageSize: number } {
  const page = Number(s.get('page'))
  const size = Number(s.get('page_size'))
  return {
    page: Number.isInteger(page) && page >= 1 && page <= 100000 ? page : 1,
    pageSize: PAGE_SIZES.includes(size) ? size : defaultPageSize,
  }
}

const scopeFromSearch = (s: URLSearchParams, fallback: 'bom' | 'all' = 'bom'): 'bom' | 'all' => {
  const v = s.get('scope')
  return v === 'all' || v === 'bom' ? v : fallback
}
const flag = (s: URLSearchParams, key: string): boolean | null => {
  const v = s.get(key)
  return v === '1' || v === 'true' ? true : v === '0' || v === 'false' ? false : null
}

/** Ghi các khóa xếp + trang chung của hai màn. */
function writeSortAndPage(
  s: URLSearchParams, sortBy: string, sortDir: 'asc' | 'desc', page: number, pageSize: number,
  defaultPageSize = PRICES_DEFAULT_PAGE_SIZE,
) {
  if (sortBy) { s.set('sort_by', sortBy); s.set('sort_dir', sortDir) }
  if (page > 1) s.set('page', String(page))
  if (pageSize !== defaultPageSize) s.set('page_size', String(pageSize))
}

// ── Bảng giá VTBB ───────────────────────────────────────────────────────────────

export interface PriceListScreenState {
  q: string
  group: string
  scope: 'bom' | 'all'
  range: { from: string; to: string }
  sortBy: string
  sortDir: 'asc' | 'desc'
  page: number
  pageSize: number
}

export function priceListScreenToSearch(st: PriceListScreenState): string {
  const s = new URLSearchParams()
  if (st.q.trim()) s.set('q', st.q.trim())
  if (st.group) s.set('group', st.group)
  if (st.scope === 'all') s.set('scope', 'all')
  if (st.range.from) s.set('date_from', st.range.from)
  if (st.range.to) s.set('date_to', st.range.to)
  writeSortAndPage(s, st.sortBy, st.sortDir, st.page, st.pageSize)
  return s.toString()
}

export function searchToPriceListScreen(search: string): PriceListScreenState {
  const s = new URLSearchParams(search)
  const sortBy = s.get('sort_by') ?? ''
  const sorted = PRICE_LIST_SORT_KEYS.includes(sortBy)
  return {
    q: textFromSearch(s, 'q'),
    group: textFromSearch(s, 'group', MAX_CODE_LENGTH),
    scope: scopeFromSearch(s),
    range: rangeFromSearch(s),
    sortBy: sorted ? sortBy : '',
    sortDir: sorted && s.get('sort_dir') === 'desc' ? 'desc' : 'asc',
    ...pageFromSearch(s),
  }
}

// ── Giá mua gần nhất ────────────────────────────────────────────────────────────

export interface LastPricesScreenState {
  filters: LastPricesFilters
  sortBy: string
  sortDir: 'asc' | 'desc'
  page: number
  pageSize: number
}

/** Khóa xếp hợp lệ khi đang hiện `n` lần: khóa cố định hoặc `p{k}_date` / `p{k}_price` với k trong 1..n. */
function validLastPricesSortKey(key: string, n: number): boolean {
  if (LAST_PRICES_SORT_KEYS.includes(key)) return true
  const m = /^p(\d+)_(date|price)$/.exec(key)
  return m !== null && Number(m[1]) >= 1 && Number(m[1]) <= n
}

export function lastPricesScreenToSearch(st: LastPricesScreenState): string {
  const f = st.filters
  const d = EMPTY_LAST_PRICES_FILTERS
  const s = new URLSearchParams()
  f.codes.forEach((c) => s.append('code', c))
  f.groups.forEach((g) => s.append('group', g))
  if (f.all) s.set('all', '1')
  if (f.n !== d.n) s.set('n', String(f.n))
  if (f.scope !== d.scope) s.set('scope', f.scope)
  f.suppliers.forEach((c) => s.append('supplier', c))
  if (f.from) s.set('date_from', f.from)
  if (f.to) s.set('date_to', f.to)
  if (f.trend !== 'all') s.set('trend', f.trend)
  if (f.minPct > 0) s.set('min_pct', String(f.minPct))
  //  `only_priced` mặc định TẮT nên chỉ ghi khi bật.
  if (f.onlyPriced !== d.onlyPriced) s.set('only_priced', '1')
  if (f.bomOnly) s.set('bom_only', '1')
  if (f.showQty) s.set('show_qty', '1')
  const isDefaultSort = st.sortBy === LAST_PRICES_DEFAULT_SORT.by && st.sortDir === LAST_PRICES_DEFAULT_SORT.dir
  writeSortAndPage(s, isDefaultSort ? '' : st.sortBy, st.sortDir, st.page, st.pageSize, LAST_PRICES_DEFAULT_PAGE_SIZE)
  return s.toString()
}

export function searchToLastPricesScreen(search: string): LastPricesScreenState {
  const s = new URLSearchParams(search)
  const n = Number(s.get('n'))
  const nShown = (LAST_PRICE_N_OPTIONS as readonly number[]).includes(n) ? n : EMPTY_LAST_PRICES_FILTERS.n
  //  Nhận cả dạng một khóa cách nhau dấu phẩy lẫn dạng lặp khóa (`supplier=a&supplier=b`) của API.
  const suppliers = [...new Set(s.getAll('supplier').flatMap((v) => v.split(',')).map((c) => c.trim())
    .filter((c) => c && c.length <= MAX_CODE_LENGTH))].slice(0, MAX_SUPPLIERS)
  //  `group` lặp khóa như `supplier` (chip nhóm bật nhiều cùng lúc); link cũ chỉ một `group=` vẫn ra đúng một nhóm.
  const groups = [...new Set(s.getAll('group').map((g) => g.trim().slice(0, MAX_CODE_LENGTH)).filter(Boolean))].slice(0, MAX_GROUPS)
  //  Mã chọn ở ô chọn mã (27/11/2026, thay ô tìm chữ `q`): `code` lặp khóa; link cũ có `q` thì bỏ qua.
  const codes = [...new Set(s.getAll('code').map((c) => c.trim()).filter((c) => c && c.length <= MAX_CODE_LENGTH))].slice(0, MAX_CODES)
  const trend = s.get('trend') as LastPricesTrend
  const minPct = Number(s.get('min_pct'))
  const sortBy = s.get('sort_by') ?? ''
  const sorted = validLastPricesSortKey(sortBy, nShown)
  const range = rangeFromSearch(s)
  //  `all=1` = đã bấm "Tất cả". Xếp khác mặc định cũng là xem rộng (chế độ gần nhất chỉ có thứ tự mới nhất trước) nên coi như "Tất cả".
  const sortDir = sorted ? (s.get('sort_dir') === 'desc' ? 'desc' : 'asc') : LAST_PRICES_DEFAULT_SORT.dir
  const sortedAwayFromRecent = sorted && (sortBy !== LAST_PRICES_DEFAULT_SORT.by || sortDir !== LAST_PRICES_DEFAULT_SORT.dir)
  return {
    filters: {
      codes,
      groups,
      all: groups.length === 0 && (flag(s, 'all') === true || sortedAwayFromRecent),
      trendAllLit: false,
      n: nShown,
      scope: scopeFromSearch(s, EMPTY_LAST_PRICES_FILTERS.scope),
      suppliers,
      from: range.from,
      to: range.to,
      trend: TRENDS.includes(trend) ? trend : 'all',
      minPct: Number.isFinite(minPct) && minPct > 0 && minPct <= 1_000_000 ? minPct : 0,
      onlyPriced: flag(s, 'only_priced') ?? EMPTY_LAST_PRICES_FILTERS.onlyPriced,
      bomOnly: flag(s, 'bom_only') ?? false,
      showQty: flag(s, 'show_qty') ?? false,
    },
    //  Không có khóa xếp hợp lệ trên URL = xếp mặc định (Lần 1 ngày mua giảm dần).
    sortBy: sorted ? sortBy : LAST_PRICES_DEFAULT_SORT.by,
    sortDir,
    ...pageFromSearch(s, LAST_PRICES_DEFAULT_PAGE_SIZE),
  }
}
