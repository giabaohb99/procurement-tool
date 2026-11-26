/**
 * duoc-CR-784 — trạng thái màn hình <-> chuỗi truy vấn của URL cho hai màn Bảng giá VTBB và Giá mua gần nhất (bản v1),
 * để F5 / gửi link vẫn giữ từ khóa, chip nhóm, phạm vi, khoảng ngày, nhà cung cấp, cột xếp và trang. Tên tham số trùng tên
 * tham số API của hai màn (và bản v2): `q` · `group` · `scope` · `only_priced` · `date_from` / `date_to` · `supplier`
 * (lặp khóa như API: `supplier=a&supplier=b`) · `n` (3 / 5 / 10) · `show_qty` · `trend` · `min_pct` · `bom_only` · `sort_by` / `sort_dir` ·
 * `page` / `page_size`. Giá trị mặc định không ghi để link gọn.
 *
 * Phần đọc coi URL là dữ liệu từ ngoài vào: khóa xếp ngoài danh sách, ngày sai lịch, n ngoài {3,5,10}, cỡ trang lạ, số quá
 * trần đều bị bỏ về mặc định, không bao giờ làm màn hỏng.
 */
import {
  EMPTY_LAST_PRICES_FILTERS, LAST_PRICE_N_OPTIONS, type LastPricesFilters,
} from './packaging-query'
import type { LastPricesTrend } from '../api/packaging-cost-types'

export const PRICES_DEFAULT_PAGE_SIZE = 50
const PAGE_SIZES = [10, 20, 50, 100]
const MAX_QUERY_LENGTH = 100
const MAX_CODE_LENGTH = 50
const MAX_SUPPLIERS = 100
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
  'q', 'group', 'scope', 'only_priced', 'date_from', 'date_to', 'supplier', 'n', 'show_qty', 'trend', 'min_pct', 'bom_only',
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

function pageFromSearch(s: URLSearchParams): { page: number; pageSize: number } {
  const page = Number(s.get('page'))
  const size = Number(s.get('page_size'))
  return {
    page: Number.isInteger(page) && page >= 1 && page <= 100000 ? page : 1,
    pageSize: PAGE_SIZES.includes(size) ? size : PRICES_DEFAULT_PAGE_SIZE,
  }
}

const scopeFromSearch = (s: URLSearchParams): 'bom' | 'all' => (s.get('scope') === 'all' ? 'all' : 'bom')
const flag = (s: URLSearchParams, key: string): boolean | null => {
  const v = s.get(key)
  return v === '1' || v === 'true' ? true : v === '0' || v === 'false' ? false : null
}

/** Ghi các khóa xếp + trang chung của hai màn. */
function writeSortAndPage(s: URLSearchParams, sortBy: string, sortDir: 'asc' | 'desc', page: number, pageSize: number) {
  if (sortBy) { s.set('sort_by', sortBy); s.set('sort_dir', sortDir) }
  if (page > 1) s.set('page', String(page))
  if (pageSize !== PRICES_DEFAULT_PAGE_SIZE) s.set('page_size', String(pageSize))
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
  if (f.q.trim()) s.set('q', f.q.trim())
  if (f.group) s.set('group', f.group)
  if (f.n !== d.n) s.set('n', String(f.n))
  if (f.scope !== d.scope) s.set('scope', f.scope)
  f.suppliers.forEach((c) => s.append('supplier', c))
  if (f.from) s.set('date_from', f.from)
  if (f.to) s.set('date_to', f.to)
  if (f.trend !== 'all') s.set('trend', f.trend)
  if (f.minPct > 0) s.set('min_pct', String(f.minPct))
  //  `only_priced` mặc định BẬT nên chỉ ghi khi tắt.
  if (f.onlyPriced !== d.onlyPriced) s.set('only_priced', '0')
  if (f.bomOnly) s.set('bom_only', '1')
  if (f.showQty) s.set('show_qty', '1')
  writeSortAndPage(s, st.sortBy, st.sortDir, st.page, st.pageSize)
  return s.toString()
}

export function searchToLastPricesScreen(search: string): LastPricesScreenState {
  const s = new URLSearchParams(search)
  const n = Number(s.get('n'))
  const nShown = (LAST_PRICE_N_OPTIONS as readonly number[]).includes(n) ? n : EMPTY_LAST_PRICES_FILTERS.n
  //  Nhận cả dạng một khóa cách nhau dấu phẩy lẫn dạng lặp khóa (`supplier=a&supplier=b`) của API.
  const suppliers = [...new Set(s.getAll('supplier').flatMap((v) => v.split(',')).map((c) => c.trim())
    .filter((c) => c && c.length <= MAX_CODE_LENGTH))].slice(0, MAX_SUPPLIERS)
  const trend = s.get('trend') as LastPricesTrend
  const minPct = Number(s.get('min_pct'))
  const sortBy = s.get('sort_by') ?? ''
  const sorted = validLastPricesSortKey(sortBy, nShown)
  const range = rangeFromSearch(s)
  return {
    filters: {
      q: textFromSearch(s, 'q'),
      group: textFromSearch(s, 'group', MAX_CODE_LENGTH),
      n: nShown,
      scope: scopeFromSearch(s),
      suppliers,
      from: range.from,
      to: range.to,
      trend: TRENDS.includes(trend) ? trend : 'all',
      minPct: Number.isFinite(minPct) && minPct > 0 && minPct <= 1_000_000 ? minPct : 0,
      onlyPriced: flag(s, 'only_priced') ?? EMPTY_LAST_PRICES_FILTERS.onlyPriced,
      bomOnly: flag(s, 'bom_only') ?? false,
      showQty: flag(s, 'show_qty') ?? false,
    },
    sortBy: sorted ? sortBy : '',
    sortDir: sorted && s.get('sort_dir') === 'desc' ? 'desc' : 'asc',
    ...pageFromSearch(s),
  }
}
