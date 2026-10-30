/**
 * Lựa chọn của "Biểu đồ linh hoạt" (duoc-CR-688, `doc/erp/hrm/05-bao-cao-nhan-su.md` §3.4):
 * vẽ theo gì, kiểu gì, bao nhiêu nhóm. Ba lựa chọn nằm trên URL để gửi đường dẫn là người
 * nhận mở đúng góc nhìn — tệp này chỉ có hàm thuần: đọc giá trị thô từ URL, suy ra lựa chọn
 * ĐANG HIỆU LỰC theo dữ liệu của trang, và dựng MỘT bản vá URL cho mỗi lần đổi.
 */

/** Vẽ theo trục thời gian (`trend[]`) hay theo chiều "Xem theo" đang chọn (`groups[]`). */
export type FlexibleChartBy = 'time' | 'group'

/** `hbar` = cột ngang, `bar` = cột dọc, `donut` = vành khuyên. */
export type FlexibleChartType = 'line' | 'bar' | 'hbar' | 'donut'

/** Số nhóm lớn nhất được vẽ riêng; `all` = vẽ hết, không gộp "Khác". */
export type FlexibleChartTop = '5' | '10' | '20' | 'all'

export interface FlexibleChartOptions {
  by: FlexibleChartBy
  type: FlexibleChartType
  top: FlexibleChartTop
}

/**
 * Tên tham số URL. ⚠️ Mọi tham số này phải bị LOẠI khỏi `queryParams` của `useReportFilters`
 * — không thì đổi kiểu biểu đồ là đổi khóa truy vấn, trang gọi lại `/summary` cho một thay
 * đổi thuần hiển thị (và tham số lạ còn rò sang đường xuất Excel, ngăn danh sách).
 */
export const FLEXIBLE_CHART_URL_PARAMS = {
  /** Chỉ số đang vẽ (= thẻ KPI đang chọn); trùng `ReportPageConfig.chartMetric` thì không ghi. */
  metric: 'chart_metric',
  by: 'chart_by',
  type: 'chart_type',
  top: 'chart_top',
} as const

export const FLEXIBLE_CHART_URL_PARAM_NAMES: ReadonlySet<string> = new Set(
  Object.values(FLEXIBLE_CHART_URL_PARAMS),
)

export const TIME_CHART_TYPES: readonly FlexibleChartType[] = ['line', 'bar']
export const GROUP_CHART_TYPES: readonly FlexibleChartType[] = ['hbar', 'bar', 'donut']
export const FLEXIBLE_CHART_TOPS: readonly FlexibleChartTop[] = ['5', '10', '20', 'all']
export const DEFAULT_FLEXIBLE_CHART_TOP: FlexibleChartTop = '10'

export const FLEXIBLE_CHART_TYPE_LABELS: Record<FlexibleChartType, string> = {
  line: 'Đường',
  bar: 'Cột',
  hbar: 'Cột ngang',
  donut: 'Vành khuyên',
}

/** Bối cảnh dữ liệu quyết định lựa chọn nào dùng được và mặc định là gì. */
export interface FlexibleChartContext {
  /** Có trục thời gian để vẽ (không `hideTrend`, chỉ số không phải `snapshot`, `trend` có mốc). */
  hasTime: boolean
  /** Có chiều "Xem theo" thật để vẽ theo nhóm. */
  hasGroup: boolean
  /** Ưu tiên vẽ theo nhóm khi URL chưa chọn: trang `hideTrend` hoặc chỉ số thời điểm. */
  preferGroup: boolean
  /** Dữ liệu nhóm hiện tại vẽ vành khuyên được (`canDrawDonut`). */
  donutAllowed: boolean
}

export interface FlexibleChartRawParams {
  by: string | null
  type: string | null
  top: string | null
}

function isOneOf<T extends string>(value: string | null, list: readonly T[]): value is T {
  return value !== null && (list as readonly string[]).includes(value)
}

/** Vẽ theo gì khi URL chưa chọn (hoặc chọn một thứ trang này không có). */
export function pickDefaultChartBy(ctx: FlexibleChartContext): FlexibleChartBy {
  if (ctx.preferGroup && ctx.hasGroup) return 'group'
  if (ctx.hasTime) return 'time'
  return ctx.hasGroup ? 'group' : 'time'
}

/** Kiểu mặc định: thời gian → đường (giữ nguyên dáng cũ); nhóm → cột ngang xếp lớn → nhỏ. */
export function pickDefaultChartType(by: FlexibleChartBy): FlexibleChartType {
  return by === 'time' ? 'line' : 'hbar'
}

/**
 * Lựa chọn ĐANG HIỆU LỰC từ giá trị thô trên URL. Giá trị lạ (gõ tay, link cũ) hoặc không
 * dùng được với dữ liệu hiện tại (vd `chart_type=donut` mà đang có 9 nhóm) âm thầm lùi về
 * mặc định — không ghi đè URL, để dữ liệu đổi lại (lọc bớt còn 4 nhóm) thì lựa chọn cũ sống lại.
 */
export function resolveFlexibleChartOptions(
  raw: FlexibleChartRawParams,
  ctx: FlexibleChartContext,
): FlexibleChartOptions {
  const available = (by: FlexibleChartBy) => (by === 'time' ? ctx.hasTime : ctx.hasGroup)
  const by: FlexibleChartBy =
    isOneOf(raw.by, ['time', 'group'] as const) && available(raw.by)
      ? raw.by
      : pickDefaultChartBy(ctx)

  const allowedTypes = by === 'time' ? TIME_CHART_TYPES : GROUP_CHART_TYPES
  const typeUsable =
    isOneOf(raw.type, allowedTypes) && (raw.type !== 'donut' || ctx.donutAllowed)
  const type = typeUsable ? (raw.type as FlexibleChartType) : pickDefaultChartType(by)

  const top = isOneOf(raw.top, FLEXIBLE_CHART_TOPS) ? raw.top : DEFAULT_FLEXIBLE_CHART_TOP
  return { by, type, top }
}

/**
 * Bản vá URL cho MỘT lần đổi — ghi cả ba tham số trong cùng một lượt `setParams` (bẫy hai
 * `setSearchParams` trong một lần bấm, xem `use-url-param-state.ts`). Đổi "Vẽ theo" mà không
 * nói kiểu thì kiểu về mặc định của trục mới (đường không có nghĩa cho nhóm). Giá trị trùng
 * mặc định thì XÓA khỏi URL — link sạch, đổi mặc định sau này không làm hỏng link cũ.
 */
export function buildFlexibleChartUrlPatch(
  current: FlexibleChartOptions,
  patch: Partial<FlexibleChartOptions>,
  ctx: FlexibleChartContext,
): Record<string, string | null> {
  const by = patch.by ?? current.by
  const byChanged = by !== current.by
  const type = patch.type ?? (byChanged ? pickDefaultChartType(by) : current.type)
  const top = patch.top ?? current.top
  return {
    [FLEXIBLE_CHART_URL_PARAMS.by]: by === pickDefaultChartBy(ctx) ? null : by,
    [FLEXIBLE_CHART_URL_PARAMS.type]: type === pickDefaultChartType(by) ? null : type,
    [FLEXIBLE_CHART_URL_PARAMS.top]: top === DEFAULT_FLEXIBLE_CHART_TOP ? null : top,
  }
}

/**
 * Chỉ số đang vẽ từ `chart_metric` trên URL. Khóa lạ (gõ tay, link cũ của báo cáo đã đổi chỉ
 * số) hoặc chỉ số PHỤ (`helper`) → về `fallback` (`config.chartMetric`). Chưa có `meta` (lượt
 * gọi đầu chưa về) thì tạm tin URL — kiểm lại ngay khi `meta` về.
 */
export function resolveChartMetric(
  raw: string | null,
  fallback: string,
  metrics: readonly { key: string; helper: boolean }[] | undefined,
): string {
  if (!raw) return fallback
  if (!metrics || metrics.length === 0) return raw
  return metrics.some((m) => m.key === raw && !m.helper) ? raw : fallback
}

/** `'all'` → `null` (không cắt), còn lại là số nhóm. */
export function parseChartTop(top: FlexibleChartTop): number | null {
  return top === 'all' ? null : Number(top)
}
