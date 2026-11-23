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
  PackagingImpactKpis,
  PackagingImpactRequest,
  PackagingMaxIncreaseProduct,
} from '../types/packaging-cost-types'
import { HISTORY_PRINT_ROW_CAP } from './packaging-history-print'
import {
  appendImpactFilterSearch,
  describeImpactAdvancedFilters,
  parseImpactFilterSearch,
} from './packaging-impact-filters'
import { formatPackagingDiff, formatPackagingPrice } from './packaging-price-format'

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

/** Phần trong ngoặc của dòng tóm tắt: "2 chai · 1 nắp · 1 mã giả định" (rỗng nếu không có gì). */
export function describeImpactSummaryDetail(kpis: PackagingImpactKpis): string {
  return [
    describeSelectedGroups(kpis.selected_by_group),
    kpis.assumed_count ? `${kpis.assumed_count} mã giả định` : '',
  ]
    .filter(Boolean)
    .join(' · ')
}

/** Ba thẻ số liệu của màn Tác động — dùng chung cho màn hình và bản in (duoc-CR-784, người chủ chốt 23/11/2026: thẻ, không phải dòng chữ). */
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
  /** Thẻ "Tăng nhiều nhất" có sản phẩm: màu số theo luật hệ (tăng chi phí = xanh). */
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
  return [
    {
      key: 'selected',
      label: 'Mã đã chọn',
      value: kpis.selected_count.toLocaleString('vi-VN'),
      unit: '',
      sub: describeImpactSummaryDetail(kpis),
      detail: '',
      tone: undefined,
      product: null,
    },
    {
      key: 'affected',
      label: 'Sản phẩm bị ảnh hưởng',
      value: kpis.affected_products.toLocaleString('vi-VN'),
      unit: '',
      sub:
        filteredTotal == null
          ? 'Dùng ít nhất 1 mã đã chọn'
          : `Đang lọc: ${filteredTotal.toLocaleString('vi-VN')} / ${kpis.affected_products.toLocaleString('vi-VN')}`,
      detail: '',
      tone: undefined,
      product: null,
    },
    {
      key: 'top-increase',
      label: 'Tăng nhiều nhất /thùng',
      value: top ? formatPackagingDiff(top.diff_carton) : IMPACT_TOP_INCREASE_EMPTY,
      unit: top ? 'VNĐ/thùng' : '',
      sub: top && top.diff_bottle != null ? `${formatPackagingDiff(top.diff_bottle)} /chai` : '',
      detail: top ? `${top.hh_code} — ${top.hh_name}` : '',
      tone: top ? 'up' : undefined,
      product: top,
    },
  ]
}
