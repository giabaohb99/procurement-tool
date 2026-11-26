/**
 * duoc-CR-784 — lựa chọn của hai màn BẢNG GIÁ VTBB và GIÁ MUA GẦN NHẤT <-> chuỗi truy vấn URL (người chủ chốt 26/11/2026):
 * F5 hay gửi link là mở lại đúng bộ lọc, cột xếp, trang và cỡ trang.
 *
 * Tên tham số = tên tham số API của hai màn (`q`, `group`, `scope`, `date_from` / `date_to`, `supplier` lặp khóa, `n`,
 * `trend`, `min_pct`, `only_priced`, `bom_only`, `show_qty`, `sort_by` / `sort_dir`, `page`, `page_size`) — cùng tên bản v1
 * dùng. Giá trị mặc định thì KHÔNG ghi lên URL; `only_priced` mặc định BẬT nên chỉ ghi khi tắt (`only_priced=0`); cờ bật
 * ghi `1`, đọc nhận `1` / `true` / `0` / `false`.
 *
 * URL là dữ liệu từ ngoài vào: ngày phải ISO đúng lịch, khóa xếp phải nằm trong bộ khóa máy chủ nhận, `n` 3 / 5 / 10, cỡ trang
 * nằm trong lựa chọn của chân bảng, chuỗi bị cắt theo `max_length` của máy chủ; thứ hỏng rơi về mặc định chứ không làm màn lỗi.
 */
import { PAGE_SIZE_OPTIONS } from '@/shared/data-table'

import type { LastPricesFilters } from '../components/packaging-last-prices-toolbar'
import type { PriceListFilters } from '../components/packaging-price-list-toolbar'
import type { LastPricesTrend } from '../types/packaging-cost-types'
import { parsePageParam } from './packaging-filter-url'
import { validDate } from './packaging-impact-print'
import { LAST_PRICE_DEFAULT_N, LAST_PRICE_N_OPTIONS, sortKeyOutsideN } from './packaging-last-prices'

/** Cỡ trang mặc định của cả hai màn. */
export const PACKAGING_LIST_DEFAULT_PAGE_SIZE = 50

const MAX_QUERY_LENGTH = 100
const MAX_GROUP_LENGTH = 50
const MAX_SUPPLIER_LENGTH = 50
const MAX_SUPPLIERS = 50
const MAX_MIN_PCT = 10_000
const LAST_PRICE_TRENDS: readonly LastPricesTrend[] = ['up', 'down', 'flat']

/** Khóa xếp Bảng giá máy chủ nhận — khớp `SORT_KEYS` của `price_list_service.py`. */
export const PRICE_LIST_SORT_KEYS: readonly string[] = [
  'code', 'name', 'group', 'unit', 'old', 'new', 'diff', 'pct', 'usage', 'purchase_count', 'last_date',
  'last_purchase_price', 'last_purchase_date', 'prev_purchase_price', 'min', 'max', 'quote_price', 'quote_from',
]

/** Khóa xếp tĩnh của Giá mua gần nhất — khớp `SORT_KEYS` của `last_prices_service.py` (còn mẫu `p{k}_price|date`). */
const LAST_PRICES_STATIC_SORT_KEYS: readonly string[] = [
  'code', 'name', 'group', 'unit', 'purchase_count', 'last_price', 'last_date', 'v12', 'v1n', 'avg',
]
const LAST_PRICES_SLOT_SORT_KEY = /^p([1-9]|10)_(price|date)$/

function validSortKey(raw: string | null, accept: (key: string) => boolean): string {
  return raw !== null && accept(raw) ? raw : ''
}

function readText(raw: string | null, maxLength: number): string {
  return (raw ?? '').trim().slice(0, maxLength)
}

function readFlag(raw: string | null, fallback: boolean): boolean {
  if (raw === '1' || raw === 'true') return true
  if (raw === '0' || raw === 'false') return false
  return fallback
}

function readPageSize(raw: string | null): number {
  const size = Number(raw)
  return (PAGE_SIZE_OPTIONS as readonly number[]).includes(size) ? size : PACKAGING_LIST_DEFAULT_PAGE_SIZE
}

function readScope(raw: string | null): 'bom' | 'all' {
  return raw === 'all' ? 'all' : 'bom'
}

/** Ghi các khóa dùng chung của hai màn: xếp, trang, cỡ trang (mặc định thì bỏ qua). */
function appendTableSearch(
  search: URLSearchParams,
  table: { sortBy: string; sortDir: 'asc' | 'desc'; page: number; pageSize: number },
): void {
  if (table.sortBy) {
    search.set('sort_by', table.sortBy)
    search.set('sort_dir', table.sortDir)
  }
  if (table.pageSize !== PACKAGING_LIST_DEFAULT_PAGE_SIZE) search.set('page_size', String(table.pageSize))
  if (table.page > 1) search.set('page', String(table.page))
}

/** Ngày đã kiểm; hai đầu ngược nhau (Từ > Đến) thì bỏ cả hai — máy chủ không có nghĩa gì cho khoảng ấy. */
function readDateRange(search: URLSearchParams): { from: string; to: string } {
  const from = validDate(search.get('date_from')) ?? ''
  const to = validDate(search.get('date_to')) ?? ''
  return from && to && from > to ? { from: '', to: '' } : { from, to }
}

// ---------------------------------------------------------------- Bảng giá VTBB

export interface PriceListUrlState {
  filters: PriceListFilters
  from: string
  to: string
  /** Rỗng = chưa chọn cột xếp. */
  sortBy: string
  sortDir: 'asc' | 'desc'
  page: number
  pageSize: number
}

export function parsePriceListUrlState(search: URLSearchParams): PriceListUrlState {
  const sortBy = validSortKey(search.get('sort_by'), (key) => PRICE_LIST_SORT_KEYS.includes(key))
  const range = readDateRange(search)
  return {
    filters: {
      q: readText(search.get('q'), MAX_QUERY_LENGTH),
      group: readText(search.get('group'), MAX_GROUP_LENGTH),
      scope: readScope(search.get('scope')),
    },
    from: range.from,
    to: range.to,
    sortBy,
    sortDir: sortBy && search.get('sort_dir') === 'desc' ? 'desc' : 'asc',
    page: parsePageParam(search.get('page')),
    pageSize: readPageSize(search.get('page_size')),
  }
}

/** Trạng thái màn → chuỗi truy vấn (không kèm `?`); mặc định thì không ghi gì. */
export function buildPriceListUrlSearch(state: PriceListUrlState): string {
  const search = new URLSearchParams()
  const q = state.filters.q.trim()
  if (q) search.set('q', q)
  if (state.filters.group) search.set('group', state.filters.group)
  if (state.filters.scope !== 'bom') search.set('scope', state.filters.scope)
  if (state.from) search.set('date_from', state.from)
  if (state.to) search.set('date_to', state.to)
  appendTableSearch(search, state)
  return search.toString()
}

// ---------------------------------------------------------------- Giá mua gần nhất

export interface LastPricesUrlState {
  filters: LastPricesFilters
  sortBy: string
  sortDir: 'asc' | 'desc'
  page: number
  pageSize: number
}

export const DEFAULT_LAST_PRICES_FILTERS: LastPricesFilters = {
  q: '',
  group: '',
  n: LAST_PRICE_DEFAULT_N,
  scope: 'bom',
  suppliers: [],
  from: '',
  to: '',
  trend: 'all',
  minPct: 0,
  onlyPriced: true,
  bomOnly: false,
  showQty: false,
}

function readLastPricesN(raw: string | null): number {
  const n = Number(raw)
  return (LAST_PRICE_N_OPTIONS as readonly number[]).includes(n) ? n : LAST_PRICE_DEFAULT_N
}

function readMinPct(raw: string | null): number {
  const pct = Number(raw)
  return raw !== null && Number.isFinite(pct) && pct > 0 && pct <= MAX_MIN_PCT ? pct : 0
}

export function parseLastPricesUrlState(search: URLSearchParams): LastPricesUrlState {
  const n = readLastPricesN(search.get('n'))
  const trend = search.get('trend')
  const range = readDateRange(search)
  //  Khóa xếp theo lần k vượt số lần đang hiện thì không còn cột để xếp (cùng luật `sortKeyOutsideN` của màn).
  const sortBy = validSortKey(
    search.get('sort_by'),
    (key) =>
      (LAST_PRICES_STATIC_SORT_KEYS.includes(key) || LAST_PRICES_SLOT_SORT_KEY.test(key)) &&
      !sortKeyOutsideN(key, n),
  )
  const suppliers = [
    ...new Set(
      search
        .getAll('supplier')
        .map((code) => readText(code, MAX_SUPPLIER_LENGTH))
        .filter(Boolean),
    ),
  ].slice(0, MAX_SUPPLIERS)
  return {
    filters: {
      q: readText(search.get('q'), MAX_QUERY_LENGTH),
      group: readText(search.get('group'), MAX_GROUP_LENGTH),
      n,
      scope: readScope(search.get('scope')),
      suppliers,
      from: range.from,
      to: range.to,
      trend: LAST_PRICE_TRENDS.includes(trend as LastPricesTrend) ? (trend as LastPricesTrend) : 'all',
      minPct: readMinPct(search.get('min_pct')),
      onlyPriced: readFlag(search.get('only_priced'), true),
      bomOnly: readFlag(search.get('bom_only'), false),
      showQty: readFlag(search.get('show_qty'), false),
    },
    sortBy,
    sortDir: sortBy && search.get('sort_dir') === 'desc' ? 'desc' : 'asc',
    page: parsePageParam(search.get('page')),
    pageSize: readPageSize(search.get('page_size')),
  }
}

/** Trạng thái màn → chuỗi truy vấn (không kèm `?`); mặc định thì không ghi gì. */
export function buildLastPricesUrlSearch(state: LastPricesUrlState): string {
  const { filters } = state
  const search = new URLSearchParams()
  const q = filters.q.trim()
  if (q) search.set('q', q)
  if (filters.group) search.set('group', filters.group)
  if (filters.n !== LAST_PRICE_DEFAULT_N) search.set('n', String(filters.n))
  if (filters.scope !== 'bom') search.set('scope', filters.scope)
  for (const code of filters.suppliers) search.append('supplier', code)
  if (filters.from) search.set('date_from', filters.from)
  if (filters.to) search.set('date_to', filters.to)
  if (filters.trend !== 'all') search.set('trend', filters.trend)
  if (filters.minPct > 0) search.set('min_pct', String(filters.minPct))
  if (!filters.onlyPriced) search.set('only_priced', '0')
  if (filters.bomOnly) search.set('bom_only', '1')
  if (filters.showQty) search.set('show_qty', '1')
  appendTableSearch(search, state)
  return search.toString()
}
