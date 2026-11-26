/**
 * duoc-CR-784 — luật thuần của LỌC NÂNG CAO bảng sản phẩm bị ảnh hưởng (màn Tác động giá, bản v1 — cùng luật với `frontend-v2/.../packaging-impact-filters.ts`): trạng thái biểu mẫu, đổi sang
 * thân `POST /impact`, đếm điều kiện đang bật, câu mô tả cho bản in, và đường đi qua chuỗi truy vấn của trang in.
 * Thanh lọc dạng chip (26/11/2026) đọc cùng trạng thái này: mỗi điều kiện = một chip, câu trên chip do `summarizeCondition`.
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
} from '../api/packaging-cost-types'
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
  /** Tên đầy đủ (menu "Thêm điều kiện", ô nhập, bản in). */
  label: string
  /** Tên ngắn đứng đầu câu trên chip ("Chênh /thùng ≥ 1.000 đ"). */
  chip: string
  unit: string
  integer?: boolean
}

const CARTON_QTY_FIELD: RangeField = { key: 'cartonQty', label: 'Quy cách thùng', chip: 'Quy cách', unit: '', integer: true }
const DIFF_BOTTLE_FIELD: RangeField = { key: 'diffBottle', label: 'Tăng/giảm /chai', chip: 'Chênh /chai', unit: 'đ' }
const DIFF_CARTON_FIELD: RangeField = { key: 'diffCarton', label: 'Tăng/giảm /thùng', chip: 'Chênh /thùng', unit: 'đ' }
const COST_NEW_FIELD: RangeField = { key: 'costNewBottle', label: 'CP bao bì/chai mới', chip: 'CP chai mới', unit: 'đ' }
const COST_OLD_FIELD: RangeField = { key: 'costOldBottle', label: 'CP bao bì/chai cũ', chip: 'CP chai cũ', unit: 'đ' }
const PCT_FIELD: RangeField = { key: 'pct', label: '% chênh', chip: '% chênh', unit: '%' }

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

/** Một điều kiện lọc của thanh chip: xu hướng · vai trò · một trong sáu khoảng số · chỉ-có-cảnh-báo. */
export type FilterConditionKey = 'trend' | 'roles' | ImpactRangeKey | 'warningsOnly'

/** Màn dùng thanh lọc nâng cao. */
export type AdvancedFilterVariant = 'impact' | 'overview'

/** Phần khác nhau giữa hai màn: ô khoảng nào, có mục xu hướng không, và cách gọi mục vai trò. */
export interface AdvancedFilterProfile {
  rangeFields: readonly RangeField[]
  showTrend: boolean
  /** Thứ tự các điều kiện trong menu "Thêm điều kiện" (và của các chip). */
  conditionOrder: readonly FilterConditionKey[]
  rolesLabel: string
  rolesAriaLabel: string
  rolesHint: string
}

export const ADVANCED_FILTER_PROFILES: Record<AdvancedFilterVariant, AdvancedFilterProfile> = {
  impact: {
    rangeFields: IMPACT_RANGE_FIELDS,
    showTrend: true,
    conditionOrder: ['trend', 'roles', 'cartonQty', 'diffBottle', 'diffCarton', 'costNewBottle', 'warningsOnly'],
    rolesLabel: 'Có mã đã chọn ở vai trò',
    rolesAriaLabel: 'Vai trò của mã đã chọn',
    rolesHint: 'Chọn nhiều vai trò = sản phẩm có mã đã chọn ở một trong các vai trò đó.',
  },
  overview: {
    rangeFields: OVERVIEW_RANGE_FIELDS,
    showTrend: false,
    conditionOrder: [
      'roles',
      'cartonQty',
      'diffBottle',
      'diffCarton',
      'costOldBottle',
      'costNewBottle',
      'pct',
      'warningsOnly',
    ],
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
 * Số điều kiện lọc nâng cao đang bật (mỗi nhóm một điều kiện) — số điều kiện đang bật của thanh lọc chip. Màn Tổng hợp
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

// ---------------------------------------------------------------------------------------------------------------------
// Thanh lọc dạng chip (26/11/2026): mỗi điều kiện đang bật là một chip; luật dưới đây dùng chung cho màn và bài kiểm.
// ---------------------------------------------------------------------------------------------------------------------

/** Câu mô tả "cảnh báo" — chỉ liệt kê các loại cảnh báo còn tồn tại (ngưỡng sàn / trần đã bỏ ở giai đoạn 04). */
export const WARNINGS_ONLY_HINT = 'Thiếu giá chai, thiếu mã / giá thành phần, thiếu quy cách thùng, lệch ĐVT.'

/** Các xu hướng chọn được trong điều kiện "Xu hướng chi phí" (không có "Tất cả" — bỏ điều kiện là xóa chip). */
export const TREND_CONDITION_VALUES: readonly Exclude<PackagingOverviewTrend, 'all'>[] = [
  'up',
  'down',
  'flat',
  'missing',
]

/** Nhãn một xu hướng (khớp chip đếm của màn Tổng hợp). */
export function trendConditionLabel(trend: PackagingOverviewTrend): string {
  return trend === 'all' ? 'Tất cả' : (TREND_TEXT[trend] ?? trend)
}

function rangeFieldOf(key: ImpactRangeKey): RangeField {
  return [...IMPACT_RANGE_FIELDS, ...OVERVIEW_RANGE_FIELDS].find((field) => field.key === key)!
}

/** Tên điều kiện trong menu "Thêm điều kiện" và trên đầu hộp sửa. */
export function conditionLabel(key: FilterConditionKey, variant: AdvancedFilterVariant): string {
  if (key === 'trend') return 'Xu hướng chi phí'
  if (key === 'roles') return ADVANCED_FILTER_PROFILES[variant].rolesLabel
  if (key === 'warningsOnly') return 'Chỉ sản phẩm có cảnh báo'
  return rangeFieldOf(key).label
}

/** Điều kiện nào đang có hiệu lực (khoảng số cần ít nhất một biên đọc được; ô nhập dở chưa tính). */
export function isConditionActive(filters: ImpactAdvancedFilters, key: FilterConditionKey): boolean {
  if (key === 'trend') return filters.trend !== 'all'
  if (key === 'roles') return filters.roles.length > 0
  if (key === 'warningsOnly') return filters.warningsOnly
  return parseRangeText(filters[key].min) != null || parseRangeText(filters[key].max) != null
}

/** Các điều kiện đang bật của màn, theo thứ tự menu. */
export function activeConditionKeys(
  filters: ImpactAdvancedFilters,
  variant: AdvancedFilterVariant,
): FilterConditionKey[] {
  return ADVANCED_FILTER_PROFILES[variant].conditionOrder.filter((key) => isConditionActive(filters, key))
}

/** Bỏ một điều kiện (xóa chip). */
export function clearCondition(filters: ImpactAdvancedFilters, key: FilterConditionKey): ImpactAdvancedFilters {
  if (key === 'trend') return { ...filters, trend: 'all' }
  if (key === 'roles') return { ...filters, roles: [] }
  if (key === 'warningsOnly') return { ...filters, warningsOnly: false }
  return { ...filters, [key]: EMPTY_RANGE }
}

/** Số trên chip theo cách viết Việt (dấu chấm ngăn nghìn, dấu phẩy thập phân). */
function formatBound(value: number): string {
  return value.toLocaleString('vi-VN', { maximumFractionDigits: 6 })
}

/**
 * Câu hiện trên chip. Khoảng số: "Chênh /thùng ≥ 1.000 đ", "Quy cách 24–40", "% chênh ≤ 5%"; khoảng ngược ("Từ" lớn hơn
 * "Đến", hoặc quy cách không nguyên) ghi thêm "(chưa áp dụng)" vì máy chủ không nhận. Ô chưa nhập số nào (chip đang mở sửa) ghi "chưa nhập".
 */
export function summarizeCondition(filters: ImpactAdvancedFilters, key: FilterConditionKey): string {
  //  Chip vừa thêm, chưa chọn gì (hộp sửa đang mở): ghi "chưa chọn" / "chưa nhập" thay vì câu rỗng.
  if (key === 'trend') {
    return `Xu hướng: ${filters.trend === 'all' ? 'chưa chọn' : trendConditionLabel(filters.trend)}`
  }
  if (key === 'roles') {
    if (filters.roles.length === 0) return 'Vai trò: chưa chọn'
    return `Vai trò: ${[...filters.roles].sort((a, b) => a - b).map((role) => roleLabel(role)).join(', ')}`
  }
  if (key === 'warningsOnly') return 'Chỉ SP có cảnh báo'
  const field = rangeFieldOf(key)
  const min = parseRangeText(filters[key].min)
  const max = parseRangeText(filters[key].max)
  if (min == null && max == null) return `${field.chip}: chưa nhập`
  //  Đơn vị tiền cách một khoảng trắng ("1.000 đ"), dấu % dính liền ("5%").
  const unit = field.unit === '%' ? '%' : field.unit ? ` ${field.unit}` : ''
  const text =
    min != null && max != null
      ? `${field.chip} ${formatBound(min)}–${formatBound(max)}${unit}`
      : min != null
        ? `${field.chip} ≥ ${formatBound(min)}${unit}`
        : `${field.chip} ≤ ${formatBound(max!)}${unit}`
  //  Khoảng ngược / quy cách không nguyên: máy chủ không nhận nên chip nói rõ là chưa lọc.
  return rangeTextProblem(key, filters[key]) ? `${text} (chưa áp dụng)` : text
}

/**
 * Lỗi của một ô khoảng đang gõ, hiện ngay dưới ô: chữ không đọc được thành số, quy cách thùng không phải số nguyên trong
 * [0; 1.000.000], hoặc "Từ" lớn hơn "Đến". `null` = ổn (kể cả ô trống). Khớp luật của `rangeBounds` / máy chủ (422).
 */
export function rangeTextProblem(key: ImpactRangeKey, range: ImpactRangeText): string | null {
  const field = rangeFieldOf(key)
  const sides = [range.min, range.max].map((text) => ({ text, value: parseRangeText(text) }))
  if (sides.some(({ text, value }) => text.trim() !== '' && value == null)) {
    return 'Nhập số hợp lệ, ví dụ 1.000 hoặc 2,5.'
  }
  if (
    field.integer &&
    sides.some(({ value }) => value != null && !(Number.isInteger(value) && value >= 0 && value <= IMPACT_CARTON_QTY_LIMIT))
  ) {
    return `Quy cách thùng phải là số nguyên từ 0 đến ${IMPACT_CARTON_QTY_LIMIT.toLocaleString('vi-VN')}.`
  }
  const [min, max] = sides.map(({ value }) => value)
  if (min != null && max != null && min > max) return '"Từ" không được lớn hơn "Đến" — điều kiện này chưa được áp dụng.'
  return null
}
