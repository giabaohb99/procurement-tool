/**
 * duoc-CR-784 — luật thuần của LỌC NÂNG CAO bảng sản phẩm bị ảnh hưởng (màn Tác động giá): trạng thái biểu mẫu, đổi sang
 * thân `POST /impact`, đếm điều kiện đang bật, câu mô tả cho bản in, và đường đi qua chuỗi truy vấn của trang in.
 *
 * Ô khoảng số giữ DẠNG CHỮ trong biểu mẫu (để người dùng gõ dở "-" hay "1," không bị nuốt) và chỉ đổi sang số khi gửi đi.
 * Khoảng có "Từ" lớn hơn "Đến" bị báo lỗi tại ô và KHÔNG gửi (máy chủ sẽ trả 422).
 *
 * Dùng chung cho HAI màn qua `AdvancedFilterVariant`: Tác động giá (`impact`, thân `POST /impact`) và Tổng hợp theo sản
 * phẩm (`overview`, tham số `GET /product-overview`; xu hướng đã có chip riêng nên không lặp trong hộp lọc).
 */
import type {
  PackagingImpactRequest,
  PackagingOverviewParams,
  PackagingOverviewTrend,
} from '../types/packaging-cost-types'
import { packagingRoleLabel } from './packaging-warning-text'

/** Vai trò thành phần (`PackagingRole`) theo thứ tự cột: Chai · Nắp · Nhãn · Nhãn thùng · Thùng. */
export const IMPACT_FILTER_ROLES: readonly number[] = [1, 2, 3, 4, 5]
/** Trần giá trị một biên — khớp `RANGE_LIMIT` của `impact_schema.py`. */
export const IMPACT_RANGE_LIMIT = 1e12
/** Trần quy cách thùng — khớp `MAX_CARTON_QTY`. */
export const IMPACT_CARTON_QTY_LIMIT = 1_000_000

export interface ImpactRangeText {
  min: string
  max: string
}

export interface ImpactAdvancedFilters {
  trend: PackagingOverviewTrend
  roles: number[]
  cartonQty: ImpactRangeText
  diffBottle: ImpactRangeText
  diffCarton: ImpactRangeText
  costNewBottle: ImpactRangeText
  /** Chỉ màn Tổng hợp theo sản phẩm dùng. */
  costOldBottle: ImpactRangeText
  pct: ImpactRangeText
  warningsOnly: boolean
}

const EMPTY_RANGE: ImpactRangeText = { min: '', max: '' }

export const EMPTY_IMPACT_FILTERS: ImpactAdvancedFilters = {
  trend: 'all',
  roles: [],
  cartonQty: EMPTY_RANGE,
  diffBottle: EMPTY_RANGE,
  diffCarton: EMPTY_RANGE,
  costNewBottle: EMPTY_RANGE,
  costOldBottle: EMPTY_RANGE,
  pct: EMPTY_RANGE,
  warningsOnly: false,
}

export type ImpactRangeKey =
  | 'cartonQty'
  | 'diffBottle'
  | 'diffCarton'
  | 'costNewBottle'
  | 'costOldBottle'
  | 'pct'

interface RangeField {
  key: ImpactRangeKey
  label: string
  unit: string
  integer?: boolean
}

const CARTON_QTY_FIELD: RangeField = { key: 'cartonQty', label: 'Quy cách thùng', unit: '', integer: true }
const DIFF_BOTTLE_FIELD: RangeField = { key: 'diffBottle', label: 'Tăng/giảm /chai', unit: 'đ' }
const DIFF_CARTON_FIELD: RangeField = { key: 'diffCarton', label: 'Tăng/giảm /thùng', unit: 'đ' }
const COST_NEW_FIELD: RangeField = { key: 'costNewBottle', label: 'CP bao bì/chai mới', unit: 'đ' }
const COST_OLD_FIELD: RangeField = { key: 'costOldBottle', label: 'CP bao bì/chai cũ', unit: 'đ' }
const PCT_FIELD: RangeField = { key: 'pct', label: '% chênh', unit: '' }

/** Nhãn + đơn vị hiện ở biểu mẫu / bản in của từng ô khoảng (Tác động giá). */
export const IMPACT_RANGE_FIELDS: readonly RangeField[] = [
  CARTON_QTY_FIELD,
  DIFF_BOTTLE_FIELD,
  DIFF_CARTON_FIELD,
  COST_NEW_FIELD,
]

/** Sáu ô khoảng của Tổng hợp theo sản phẩm, theo thứ tự cột của bảng. */
export const OVERVIEW_RANGE_FIELDS: readonly RangeField[] = [
  CARTON_QTY_FIELD,
  COST_OLD_FIELD,
  COST_NEW_FIELD,
  DIFF_BOTTLE_FIELD,
  DIFF_CARTON_FIELD,
  PCT_FIELD,
]

/** Màn dùng hộp lọc nâng cao. */
export type AdvancedFilterVariant = 'impact' | 'overview'

/** Phần khác nhau giữa hai màn: ô khoảng nào, có mục xu hướng không, và cách gọi mục vai trò. */
export interface AdvancedFilterProfile {
  rangeFields: readonly RangeField[]
  showTrend: boolean
  rolesLabel: string
  rolesAriaLabel: string
  rolesHint: string
}

export const ADVANCED_FILTER_PROFILES: Record<AdvancedFilterVariant, AdvancedFilterProfile> = {
  impact: {
    rangeFields: IMPACT_RANGE_FIELDS,
    showTrend: true,
    rolesLabel: 'Có mã đã chọn ở vai trò',
    rolesAriaLabel: 'Vai trò của mã đã chọn',
    rolesHint: 'Chọn nhiều vai trò = sản phẩm có mã đã chọn ở một trong các vai trò đó.',
  },
  overview: {
    rangeFields: OVERVIEW_RANGE_FIELDS,
    showTrend: false,
    rolesLabel: 'Có mã ở vai trò',
    rolesAriaLabel: 'Vai trò của mã trong định mức',
    rolesHint: 'Chọn nhiều vai trò = sản phẩm có mã ở một trong các vai trò đó trong định mức.',
  },
}

/**
 * Chữ người gõ → số. Theo cách viết Việt: dấu chấm ngăn nghìn (bỏ), dấu phẩy là thập phân. Rỗng / không phải số hữu hạn /
 * vượt trần → `null` (coi là chưa nhập). Cho phép dấu trừ đầu (chênh lệch giảm là số âm).
 */
export function parseRangeText(text: string): number | null {
  const cleaned = text.trim().replace(/\s/g, '').replace(/\./g, '').replace(',', '.')
  if (!/^-?\d+(\.\d+)?$/.test(cleaned)) return null
  const value = Number(cleaned)
  return Number.isFinite(value) && Math.abs(value) <= IMPACT_RANGE_LIMIT ? value : null
}

function rangeBounds(range: ImpactRangeText, integer: boolean) {
  const clean = (text: string) => {
    const value = parseRangeText(text)
    if (value == null) return undefined
    return integer ? (Number.isInteger(value) && value >= 0 && value <= IMPACT_CARTON_QTY_LIMIT ? value : undefined) : value
  }
  return { min: clean(range.min), max: clean(range.max) }
}

/** Khóa các ô khoảng có "Từ" > "Đến" (báo lỗi tại ô, không gửi máy chủ). */
export function invalidImpactRanges(
  filters: ImpactAdvancedFilters,
  fields: readonly RangeField[] = IMPACT_RANGE_FIELDS,
): ImpactRangeKey[] {
  return fields.filter(({ key, integer }) => {
    const { min, max } = rangeBounds(filters[key], Boolean(integer))
    return min != null && max != null && min > max
  }).map(({ key }) => key)
}

/** Các ô khoảng → cặp trường `_min` / `_max` của yêu cầu (bỏ ô trống, ô không hợp lệ, ô có Từ > Đến). */
function rangesToRequest(
  filters: ImpactAdvancedFilters,
  fields: readonly RangeField[] = IMPACT_RANGE_FIELDS,
): Record<string, number> {
  const bad = new Set(invalidImpactRanges(filters, fields))
  const out: Record<string, number> = {}
  for (const { key, integer } of fields) {
    if (bad.has(key)) continue
    const { min, max } = rangeBounds(filters[key], Boolean(integer))
    const field = RANGE_REQUEST_FIELD[key]
    if (min != null) out[`${field}_min`] = min
    if (max != null) out[`${field}_max`] = max
  }
  return out
}

const RANGE_REQUEST_FIELD: Record<ImpactRangeKey, string> = {
  cartonQty: 'carton_qty',
  diffBottle: 'diff_bottle',
  diffCarton: 'diff_carton',
  costNewBottle: 'cost_new_bottle',
  costOldBottle: 'cost_old_bottle',
  pct: 'pct',
}

/** Bộ lọc biểu mẫu → các trường của thân `POST /impact` (chỉ trường có giá trị hợp lệ). */
export function impactFiltersToRequest(
  filters: ImpactAdvancedFilters,
): Partial<PackagingImpactRequest> {
  const out: Partial<PackagingImpactRequest> = rangesToRequest(filters) as Partial<PackagingImpactRequest>
  if (filters.trend !== 'all') out.trend = filters.trend
  if (filters.roles.length) out.part_roles = [...filters.roles].sort((a, b) => a - b)
  if (filters.warningsOnly) out.warnings_only = true
  return out
}

/**
 * Số điều kiện lọc nâng cao đang bật (mỗi nhóm một điều kiện) — số trên huy hiệu của nút "Lọc nâng cao". Màn Tổng hợp
 * không đếm xu hướng (chip riêng đã hiện trạng thái đang chọn).
 */
export function countAdvancedFilters(
  filters: ImpactAdvancedFilters,
  variant: AdvancedFilterVariant = 'impact',
): number {
  const profile = ADVANCED_FILTER_PROFILES[variant]
  const ranges = rangesToRequest(filters, profile.rangeFields)
  const rangeGroups = profile.rangeFields.filter(
    ({ key }) =>
      ranges[`${RANGE_REQUEST_FIELD[key]}_min`] !== undefined ||
      ranges[`${RANGE_REQUEST_FIELD[key]}_max`] !== undefined,
  ).length
  return (
    rangeGroups +
    (profile.showTrend && filters.trend !== 'all' ? 1 : 0) +
    (filters.roles.length > 0 ? 1 : 0) +
    (filters.warningsOnly ? 1 : 0)
  )
}

/** Số điều kiện đang bật của màn Tác động giá. */
export function countImpactFilters(filters: ImpactAdvancedFilters): number {
  return countAdvancedFilters(filters, 'impact')
}

/**
 * Bộ lọc biểu mẫu → tham số `GET /product-overview` (chỉ trường có giá trị hợp lệ). Xu hướng KHÔNG nằm ở đây: nó đi bằng
 * chip riêng của màn. `part_roles` là chuỗi `1,5` (GET không có thân; máy chủ nhận dấu phẩy).
 */
export function overviewFiltersToParams(filters: ImpactAdvancedFilters): Partial<PackagingOverviewParams> {
  const out = rangesToRequest(filters, OVERVIEW_RANGE_FIELDS) as Partial<PackagingOverviewParams>
  if (filters.roles.length) out.part_roles = [...filters.roles].sort((a, b) => a - b).join(',')
  if (filters.warningsOnly) out.warnings_only = true
  return out
}

/** Các khóa của thân yêu cầu thuộc lọc nâng cao (để bản in / bài kiểm liệt kê một chỗ). */
export const IMPACT_FILTER_REQUEST_KEYS = [
  'trend',
  'part_roles',
  'carton_qty_min',
  'carton_qty_max',
  'diff_bottle_min',
  'diff_bottle_max',
  'diff_carton_min',
  'diff_carton_max',
  'cost_new_bottle_min',
  'cost_new_bottle_max',
  'warnings_only',
] as const satisfies readonly (keyof PackagingImpactRequest)[]

const TREND_VALUES: readonly string[] = ['up', 'down', 'flat', 'missing']
const TREND_TEXT: Record<string, string> = {
  up: 'Tăng',
  down: 'Giảm',
  flat: 'Không đổi',
  missing: 'Chưa có giá',
}

/** Chuỗi truy vấn của bản in → trường lọc nâng cao của thân yêu cầu (đã kiểm: URL là dữ liệu từ ngoài vào). */
export function parseImpactFilterSearch(search: URLSearchParams): Partial<PackagingImpactRequest> {
  const out: Partial<PackagingImpactRequest> = {}
  const trend = search.get('trend')
  if (trend && TREND_VALUES.includes(trend)) out.trend = trend as PackagingImpactRequest['trend']
  const roles = (search.get('part_roles') ?? '')
    .split(',')
    .map((item) => Number(item))
    .filter((role) => IMPACT_FILTER_ROLES.includes(role))
  if (roles.length) out.part_roles = [...new Set(roles)].sort((a, b) => a - b)
  if (search.get('warnings_only') === '1') out.warnings_only = true
  //  Biên trên URL là số trần kiểu máy ("1234.5") — đi qua cùng bộ kiểm với ô nhập (đổi dấu thập phân về kiểu Việt).
  const text = (field: string): ImpactRangeText => ({
    min: (search.get(`${field}_min`) ?? '').replace('.', ','),
    max: (search.get(`${field}_max`) ?? '').replace('.', ','),
  })
  return Object.assign(
    out,
    rangesToRequest({
      ...EMPTY_IMPACT_FILTERS,
      cartonQty: text('carton_qty'),
      diffBottle: text('diff_bottle'),
      diffCarton: text('diff_carton'),
      costNewBottle: text('cost_new_bottle'),
    }),
  )
}

/** Trường lọc nâng cao của thân yêu cầu → các cặp `khóa=giá trị` của chuỗi truy vấn trang in. */
export function appendImpactFilterSearch(search: URLSearchParams, request: PackagingImpactRequest): void {
  if (request.trend) search.set('trend', request.trend)
  if (request.part_roles?.length) search.set('part_roles', request.part_roles.join(','))
  if (request.warnings_only) search.set('warnings_only', '1')
  for (const key of IMPACT_FILTER_REQUEST_KEYS) {
    if (!key.endsWith('_min') && !key.endsWith('_max')) continue
    const value = request[key]
    if (typeof value === 'number') search.set(key, String(value))
  }
}

function rangeText(label: string, unit: string, min?: number, max?: number): string | null {
  if (min == null && max == null) return null
  const fmt = (n: number) => n.toLocaleString('vi-VN')
  const span = min != null && max != null ? `${fmt(min)} – ${fmt(max)}` : min != null ? `từ ${fmt(min)}` : `đến ${fmt(max!)}`
  return `${label}: ${span} ${unit}`
}

/** Các mảnh mô tả bộ lọc nâng cao cho dòng "Bộ lọc" của bản in. */
export function describeImpactAdvancedFilters(request: PackagingImpactRequest): string[] {
  const parts: (string | null)[] = [
    request.trend ? `Xu hướng: ${TREND_TEXT[request.trend]}` : null,
    request.part_roles?.length
      ? `Mã đã chọn ở vai trò: ${request.part_roles.map((role) => packagingRoleLabel(role)).join(', ')}`
      : null,
    rangeText('Quy cách thùng', 'chai/thùng', request.carton_qty_min, request.carton_qty_max),
    rangeText('Tăng/giảm /chai', 'đ', request.diff_bottle_min, request.diff_bottle_max),
    rangeText('Tăng/giảm /thùng', 'đ', request.diff_carton_min, request.diff_carton_max),
    rangeText('CP bao bì/chai mới', 'đ', request.cost_new_bottle_min, request.cost_new_bottle_max),
    request.warnings_only ? 'Chỉ sản phẩm có cảnh báo' : null,
  ]
  return parts.filter((part): part is string => part != null)
}
