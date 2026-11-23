/**
 * duoc-CR-784 — luật thuần của BẢN IN Tác động giá bao bì: thân `POST /impact` <-> chuỗi truy vấn của trang in, câu mô tả
 * bộ lọc, dòng tóm tắt. Cùng nếp với `packaging-history-print.ts`: URL là dữ liệu từ ngoài vào nên mọi trường được kiểm ở
 * đây trước khi gửi máy chủ.
 *
 * Giá giả định đi bằng các khóa `assumed=MÃ:GIÁ` lặp lại (tách ở dấu hai chấm CUỐI, vì mã có thể chứa dấu hai chấm).
 */
import { appRoutes } from '@/shared/constants/app-routes'
import { formatDate } from '@/shared/utils/format-date'

import type {
  PackagingImpactRequest,
} from '../types/packaging-cost-types'
import { HISTORY_PRINT_ROW_CAP } from './packaging-history-print'
import {
  appendImpactFilterSearch,
  describeImpactAdvancedFilters,
  parseImpactFilterSearch,
} from './packaging-impact-filters'
import { formatPackagingPrice } from './packaging-price-format'

/** Trần số dòng sản phẩm của một bản in — cùng trần với Lịch sử mua hàng. */
export const IMPACT_PRINT_ROW_CAP = HISTORY_PRINT_ROW_CAP
/** Trần số mã một lượt tính — khớp `MAX_CODES` của `impact_schema.py`. */
export const IMPACT_PRINT_MAX_CODES = 500
/** Mã dài hơn thì máy chủ trả 422 (`Str50`), bỏ ngay từ URL. */
const MAX_CODE_LENGTH = 50
/** Cỡ một lượt nạp bảng sản phẩm của bản in = trần `MAX_PAGE_SIZE` của máy chủ. */
export const IMPACT_PRINT_PAGE_SIZE = 500
/** Trần ô tìm sản phẩm — khớp `max_length=100` của máy chủ. */
const MAX_QUERY_LENGTH = 100

/** Khóa xếp bảng sản phẩm máy chủ nhận — khớp `SORT_GETTERS` của `impact_service.py`. */
export const IMPACT_SORT_KEYS: readonly string[] = [
  'hh_code',
  'hh_name',
  'carton_qty',
  'cost_old_bottle',
  'cost_applied_bottle',
  'diff_bottle',
  'diff_carton',
  'cost_old_carton',
  'cost_applied_carton',
  'pct',
  'trend',
  //  Năm cột thành phần: xếp theo giá đang áp của thành phần (hòa theo mã thành phần rồi mã HH).
  'part_bottle',
  'part_cap',
  'part_label',
  'part_carton_label',
  'part_carton',
]

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/

function validDate(raw: string | null): string | undefined {
  if (!raw || !ISO_DATE.test(raw)) return undefined
  const time = Date.parse(`${raw}T00:00:00Z`)
  return Number.isNaN(time) || new Date(time).toISOString().slice(0, 10) !== raw ? undefined : raw
}

/** Thân tính (chưa kèm trang) -> chuỗi truy vấn của trang in. */
export function buildImpactPrintSearch(request: PackagingImpactRequest): string {
  const search = new URLSearchParams()
  search.set('codes', request.codes.join(','))
  for (const [code, price] of Object.entries(request.assumed_prices ?? {})) {
    search.append('assumed', `${code}:${price}`)
  }
  if (request.date_from) search.set('date_from', request.date_from)
  if (request.date_to) search.set('date_to', request.date_to)
  if (request.q) search.set('q', request.q)
  if (request.sort_by) {
    search.set('sort_by', request.sort_by)
    search.set('sort_dir', request.sort_dir ?? 'asc')
  }
  appendImpactFilterSearch(search, request)
  return search.toString()
}

export function packagingImpactPrintHref(request: PackagingImpactRequest): string {
  return `${appRoutes.procurement.packagingImpactPrint}?${buildImpactPrintSearch(request)}`
}

/**
 * Chuỗi truy vấn -> thân `POST /impact`. `codes` rỗng nghĩa là link hỏng: trang in báo "chưa chọn mã" thay vì gọi máy
 * chủ. Giá giả định chỉ nhận cho mã đang chọn, số hữu hạn và > 0 (0 / âm / chữ bị bỏ — giá bao bì 0 đồng không phải mô phỏng).
 */
export function parseImpactPrintSearch(search: URLSearchParams): PackagingImpactRequest {
  const codes = [
    ...new Set(
      (search.get('codes') ?? '')
        .split(',')
        .map((code) => code.trim())
        .filter((code) => code && code.length <= MAX_CODE_LENGTH),
    ),
  ].slice(0, IMPACT_PRINT_MAX_CODES)
  const picked = new Set(codes)
  const assumed: Record<string, number> = {}
  for (const pair of search.getAll('assumed')) {
    const cut = pair.lastIndexOf(':')
    if (cut <= 0) continue
    const code = pair.slice(0, cut).trim()
    const price = Number(pair.slice(cut + 1))
    if (picked.has(code) && Number.isFinite(price) && price > 0) assumed[code] = price
  }
  const q = (search.get('q') ?? '').trim().slice(0, MAX_QUERY_LENGTH)
  const sortBy = search.get('sort_by')
  const sorted = sortBy !== null && IMPACT_SORT_KEYS.includes(sortBy)
  return {
    codes,
    assumed_prices: Object.keys(assumed).length ? assumed : undefined,
    date_from: validDate(search.get('date_from')),
    date_to: validDate(search.get('date_to')),
    q: q || undefined,
    ...parseImpactFilterSearch(search),
    ...(sorted ? { sort_by: sortBy, sort_dir: search.get('sort_dir') === 'desc' ? 'desc' : 'asc' } : {}),
  }
}

/** Các mảnh của dòng mô tả bộ lọc — CHỈ điều kiện ngoài danh sách mã (mã đã chọn có ô chip riêng): giá giả định, khoảng ngày tính min–max, từ khóa. */
export function describeImpactFilters(request: PackagingImpactRequest): string[] {
  const parts: string[] = []
  const assumed = Object.entries(request.assumed_prices ?? {})
  if (assumed.length) {
    parts.push(
      `Giá giả định: ${assumed.map(([code, price]) => `${code} = ${formatPackagingPrice(price)}`).join(', ')}`,
    )
  }
  const { date_from: from, date_to: to } = request
  if (from || to) {
    const range = from && to ? `${formatDate(from)} – ${formatDate(to)}` : from ? `từ ${formatDate(from)}` : `đến ${formatDate(to)}`
    parts.push(`Khoảng ngày tính min – max: ${range}`)
  }
  if (request.q) parts.push(`Tìm sản phẩm: "${request.q}"`)
  parts.push(...describeImpactAdvancedFilters(request))
  return parts
}

/** "2 chai · 1 nắp" — số mã đã chọn theo nhóm. */
export function describeSelectedGroups(byGroup: Record<string, number> | undefined): string {
  return Object.entries(byGroup ?? {})
    .map(([group, count]) => `${count} ${group.toLowerCase()}`)
    .join(' · ')
}

