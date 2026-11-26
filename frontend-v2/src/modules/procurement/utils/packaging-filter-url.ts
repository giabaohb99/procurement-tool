/**
 * duoc-CR-784 — LỌC NÂNG CAO (thanh chip) của Tác động giá và Tổng hợp theo sản phẩm <-> chuỗi truy vấn URL, để F5 / gửi
 * link giữ nguyên bộ lọc. Tên tham số = tên trường máy chủ nhận (`part_roles`, `carton_qty_min`, `diff_bottle_max`,
 * `pct_min`, `warnings_only`, `trend`…) — cùng tên bản v1 dùng, cùng tên bản in đọc.
 *
 * URL là dữ liệu từ ngoài vào: biên số đọc qua đúng bộ kiểm của ô nhập (`parseRangeText`), vai trò lạ / xu hướng lạ bị
 * bỏ; giá trị hỏng trả ô trống chứ không làm màn lỗi.
 */
import type { PackagingOverviewTrend } from '../types/packaging-cost-types'
import {
  ADVANCED_FILTER_PROFILES,
  EMPTY_IMPACT_FILTERS,
  IMPACT_FILTER_ROLES,
  RANGE_REQUEST_FIELD,
  impactFiltersToRequest,
  overviewFiltersToParams,
  parseRangeText,
  type AdvancedFilterVariant,
  type ImpactAdvancedFilters,
  type ImpactRangeText,
} from './packaging-impact-filters'

const TRENDS: readonly PackagingOverviewTrend[] = ['up', 'down', 'flat', 'missing']

/** `trend` của URL; lạ hoặc thiếu → `all`. */
export function parseTrendParam(raw: string | null): PackagingOverviewTrend {
  return TRENDS.includes(raw as PackagingOverviewTrend) ? (raw as PackagingOverviewTrend) : 'all'
}

/** Biên số trên URL là số kiểu máy ("1234.5") → chữ kiểu ô nhập ("1234,5"); không đọc được thì ô trống. */
function boundText(raw: string | null): string {
  if (raw == null) return ''
  const text = raw.trim().replace('.', ',')
  return parseRangeText(text) == null ? '' : text
}

/** Chuỗi truy vấn → bộ lọc biểu mẫu của màn (`variant` quyết định ô khoảng nào được đọc). */
export function advancedFiltersFromSearch(
  search: URLSearchParams,
  variant: AdvancedFilterVariant,
): ImpactAdvancedFilters {
  const profile = ADVANCED_FILTER_PROFILES[variant]
  const roles = (search.get('part_roles') ?? '')
    .split(',')
    .map((item) => Number(item))
    .filter((role) => IMPACT_FILTER_ROLES.includes(role))
  const filters: ImpactAdvancedFilters = {
    ...EMPTY_IMPACT_FILTERS,
    trend: profile.showTrend ? parseTrendParam(search.get('trend')) : 'all',
    roles: [...new Set(roles)].sort((a, b) => a - b),
    warningsOnly: ['1', 'true'].includes(search.get('warnings_only') ?? ''),
  }
  for (const { key } of profile.rangeFields) {
    const field = RANGE_REQUEST_FIELD[key]
    const range: ImpactRangeText = {
      min: boundText(search.get(`${field}_min`)),
      max: boundText(search.get(`${field}_max`)),
    }
    filters[key] = range
  }
  return filters
}

/**
 * Bộ lọc biểu mẫu → các cặp khóa của URL. Đi qua đúng hàm dựng thân yêu cầu (`impactFiltersToRequest` /
 * `overviewFiltersToParams`) nên URL chỉ chứa thứ máy chủ thật sự nhận: ô nhập dở, khoảng Từ > Đến không lên URL.
 * Màn Tổng hợp tự ghi `trend` (chip riêng), nên ở đây chỉ màn Tác động ghi.
 */
export function appendAdvancedFiltersSearch(
  search: URLSearchParams,
  filters: ImpactAdvancedFilters,
  variant: AdvancedFilterVariant,
): void {
  const values: Record<string, unknown> =
    variant === 'impact' ? impactFiltersToRequest(filters) : overviewFiltersToParams(filters)
  for (const [key, value] of Object.entries(values)) {
    if (value === undefined || value === false) continue
    if (key === 'part_roles') search.set(key, Array.isArray(value) ? value.join(',') : String(value))
    else if (key === 'warnings_only') search.set(key, '1')
    else search.set(key, String(value))
  }
}

/** Trang trên URL: số nguyên dương; hỏng / thiếu → 1. */
export function parsePageParam(raw: string | null): number {
  const page = Number(raw)
  return Number.isInteger(page) && page >= 1 && page <= 100_000 ? page : 1
}
