/**
 * duoc-CR-784 — luật thuần của LỌC NÂNG CAO bảng sản phẩm bị ảnh hưởng (màn Tác động giá, bản v1 — cùng luật với `frontend-v2/.../packaging-impact-filters.ts`): trạng thái biểu mẫu, đổi sang
 * thân `POST /impact`, đếm điều kiện đang bật, câu mô tả cho bản in, và đường đi qua chuỗi truy vấn của trang in.
 *
 * Ô khoảng số giữ DẠNG CHỮ trong biểu mẫu (để người dùng gõ dở "-" hay "1," không bị nuốt) và chỉ đổi sang số khi gửi đi.
 * Khoảng có "Từ" lớn hơn "Đến" bị báo lỗi tại ô và KHÔNG gửi (máy chủ sẽ trả 422).
 */
import type { PackagingImpactRequest, PackagingOverviewTrend } from '../api/packaging-cost-types'
import { roleLabel } from './packaging-price'

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
  warningsOnly: false,
}

export type ImpactRangeKey = 'cartonQty' | 'diffBottle' | 'diffCarton' | 'costNewBottle'

/** Nhãn + đơn vị hiện ở biểu mẫu / bản in của từng ô khoảng. */
export const IMPACT_RANGE_FIELDS: readonly {
  key: ImpactRangeKey
  label: string
  unit: string
  integer?: boolean
}[] = [
  { key: 'cartonQty', label: 'Quy cách thùng', unit: '', integer: true },
  { key: 'diffBottle', label: 'Tăng/giảm /chai', unit: 'đ' },
  { key: 'diffCarton', label: 'Tăng/giảm /thùng', unit: 'đ' },
  { key: 'costNewBottle', label: 'CP bao bì/chai mới', unit: 'đ' },
]

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
export function invalidImpactRanges(filters: ImpactAdvancedFilters): ImpactRangeKey[] {
  return IMPACT_RANGE_FIELDS.filter(({ key, integer }) => {
    const { min, max } = rangeBounds(filters[key], Boolean(integer))
    return min != null && max != null && min > max
  }).map(({ key }) => key)
}

/** Bốn ô khoảng → cặp trường `_min` / `_max` của thân yêu cầu (bỏ ô trống, ô không hợp lệ, ô có Từ > Đến). */
function rangesToRequest(filters: ImpactAdvancedFilters): Partial<PackagingImpactRequest> {
  const bad = new Set(invalidImpactRanges(filters))
  const out: Record<string, number> = {}
  for (const { key, integer } of IMPACT_RANGE_FIELDS) {
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
}

/** Bộ lọc biểu mẫu → các trường của thân `POST /impact` (chỉ trường có giá trị hợp lệ). */
export function impactFiltersToRequest(
  filters: ImpactAdvancedFilters,
): Partial<PackagingImpactRequest> {
  const out: Partial<PackagingImpactRequest> = rangesToRequest(filters)
  if (filters.trend !== 'all') out.trend = filters.trend
  if (filters.roles.length) out.part_roles = [...filters.roles].sort((a, b) => a - b)
  if (filters.warningsOnly) out.warnings_only = true
  return out
}

/** Số điều kiện lọc nâng cao đang bật (mỗi nhóm một điều kiện) — số trên huy hiệu của nút "Lọc nâng cao". */
export function countImpactFilters(filters: ImpactAdvancedFilters): number {
  const request = impactFiltersToRequest(filters)
  const has = (...keys: (keyof PackagingImpactRequest)[]) => keys.some((key) => request[key] !== undefined)
  return [
    has('trend'),
    has('part_roles'),
    has('carton_qty_min', 'carton_qty_max'),
    has('diff_bottle_min', 'diff_bottle_max'),
    has('diff_carton_min', 'diff_carton_max'),
    has('cost_new_bottle_min', 'cost_new_bottle_max'),
    has('warnings_only'),
  ].filter(Boolean).length
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
      ? `Mã đã chọn ở vai trò: ${request.part_roles.map((role) => roleLabel(role)).join(', ')}`
      : null,
    rangeText('Quy cách thùng', 'chai/thùng', request.carton_qty_min, request.carton_qty_max),
    rangeText('Tăng/giảm /chai', 'đ', request.diff_bottle_min, request.diff_bottle_max),
    rangeText('Tăng/giảm /thùng', 'đ', request.diff_carton_min, request.diff_carton_max),
    rangeText('CP bao bì/chai mới', 'đ', request.cost_new_bottle_min, request.cost_new_bottle_max),
    request.warnings_only ? 'Chỉ sản phẩm có cảnh báo' : null,
  ]
  return parts.filter((part): part is string => part != null)
}
