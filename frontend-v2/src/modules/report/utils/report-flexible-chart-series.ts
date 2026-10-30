import type { ComparisonChartPoint } from '../components/period-comparison-chart'
import type {
  ReportCompareMode,
  ReportGroupRow,
  ReportMetricMeta,
  ReportTrendPoint,
} from '../types/report-analytics'
import { isMetricValuesSuppressed, REPORT_OTHER_GROUP_KEY } from './build-report-table-rows'

/** Khóa của phần dư Top N do CHÍNH biểu đồ gộp — khác `__other__` máy chủ gộp sẵn. */
export const FLEXIBLE_CHART_REST_KEY = '__chart_rest__'
export const FLEXIBLE_CHART_REST_LABEL = 'Khác'

/** Hai thuộc tính của chỉ số quyết định có cộng gộp được không. */
export type FlexibleMetricTraits = Pick<ReportMetricMeta, 'kind' | 'additive'>

/**
 * Cộng các nhóm có ra đúng phần gộp không: cờ `additive` của máy chủ quyết; thiếu cờ (bản cũ)
 * thì coi là cộng được, riêng `percent` vẫn không (cộng các tỷ lệ ra con số vô nghĩa).
 */
export function isMetricAdditive(traits: FlexibleMetricTraits): boolean {
  if (traits.additive === false) return false
  return traits.kind !== 'percent'
}

/** Vành khuyên chỉ đọc được khi có tối đa chừng này lát (§3.4: "tròn chỉ khi ≤ 6 nhóm"). */
export const DONUT_MAX_GROUPS = 6

export interface FlexibleGroupItem {
  key: string
  label: string
  value: number
  /** Phần dư Top N gộp lại — không phải một nhóm thật, không mở danh sách được. */
  isRest: boolean
}

export interface FlexibleGroupSeries {
  items: FlexibleGroupItem[]
  /** Số nhóm vẽ được (có số) TRƯỚC khi cắt Top N — dùng để xét vành khuyên. */
  drawableCount: number
  /** Nhóm bị máy chủ che (mọi số `null`, vd nhóm dưới 3 người) — không vẽ, chỉ đếm. */
  suppressedCount: number
  /** Có hàng `__other__` (máy chủ gộp khi vượt trần nhóm) bị bỏ khỏi biểu đồ. */
  skippedServerOther: boolean
  /** Có nhóm nhưng KHÔNG nhóm nào mang khóa chỉ số này (chỉ số chỉ có ở dòng Tổng). */
  metricMissing: boolean
  /** Nhóm có số 0 — không vẽ (cột rỗng chỉ chiếm chỗ), chỉ đếm để ghi chú. */
  zeroCount: number
  /** Phần dư Top N bị BỎ (không gộp) vì chỉ số không cộng được (tỷ lệ, bình quân…). */
  droppedRestCount: number
}

/**
 * Mốc của trục thời gian — ĐÚNG như `ReportTrendChart` cũ dựng, để mặc định của biểu đồ linh
 * hoạt trông y hệt trước. `compare=none` thì không có đường kỳ trước.
 */
export function buildFlexibleTimeSeries(
  trend: ReportTrendPoint[],
  metric: string,
  compareMode: ReportCompareMode,
): ComparisonChartPoint[] {
  return trend.map((point) => ({
    label: point.label,
    current: point.current[metric] ?? null,
    previous: compareMode === 'none' ? null : (point.compare?.[metric] ?? null),
  }))
}

/**
 * Dãy nhóm để vẽ theo chiều "Xem theo": bỏ nhóm bị che (`null`) và hàng `__other__` của máy
 * chủ, xếp lớn → nhỏ, giữ `top` nhóm đầu, phần dư gộp thành "Khác".
 *
 * - Giá trị `null` lẻ ở một nhóm KHÔNG bị che (chỉ số dẫn xuất mẫu số 0) → bỏ, không đếm là "che".
 * - Số 0 → không vẽ (ở màn Hợp đồng lao động 18/19 phòng ban là 0: một cột thật giữa 18 dòng
 *   trống), chỉ đếm vào ghi chú "N nhóm bằng 0". Biểu đồ đọc độ lớn, bảng "Xem theo" vẫn đủ dòng.
 * - Chỉ số không cộng được (`isMetricAdditive` sai: tỷ lệ, bình quân, đếm phân biệt, min/max)
 *   → phần dư bị BỎ thay vì gộp: tổng của chúng là một con số sai.
 */
export function buildFlexibleGroupSeries(
  groups: ReportGroupRow[],
  metric: string,
  top: number | null,
  traits: FlexibleMetricTraits,
): FlexibleGroupSeries {
  let suppressedCount = 0
  let zeroCount = 0
  let skippedServerOther = false
  let hasMetricKey = false
  const drawable: FlexibleGroupItem[] = []

  for (const g of groups) {
    if (metric in g.current) hasMetricKey = true
    if (g.key === REPORT_OTHER_GROUP_KEY) {
      skippedServerOther = true
      continue
    }
    if (isMetricValuesSuppressed(g.current)) {
      suppressedCount += 1
      continue
    }
    const value = g.current[metric]
    if (typeof value !== 'number' || !Number.isFinite(value)) continue
    if (value === 0) {
      zeroCount += 1
      continue
    }
    drawable.push({ key: g.key, label: g.label, value, isRest: false })
  }

  drawable.sort((a, b) => b.value - a.value)
  const cut = top !== null && top > 0 && drawable.length > top
  const head = cut ? drawable.slice(0, top) : drawable
  const rest = cut ? drawable.slice(top) : []

  let items = head
  let droppedRestCount = 0
  if (rest.length > 0) {
    if (!isMetricAdditive(traits)) {
      droppedRestCount = rest.length
    } else {
      const sum = rest.reduce((acc, item) => acc + item.value, 0)
      items = [
        ...head,
        {
          key: FLEXIBLE_CHART_REST_KEY,
          label: `${FLEXIBLE_CHART_REST_LABEL} (${rest.length} nhóm)`,
          value: sum,
          isRest: true,
        },
      ]
    }
  }

  return {
    items,
    drawableCount: drawable.length,
    suppressedCount,
    zeroCount,
    skippedServerOther,
    metricMissing: groups.length > 0 && !hasMetricKey,
    droppedRestCount,
  }
}

/**
 * Vành khuyên chỉ hợp khi đang nói "phần trên tổng": tối đa 6 nhóm có số, không số âm, tổng
 * dương, và chỉ số CỘNG ĐƯỢC (miếng bánh của các tỷ lệ / bình quân cộng lại không ra 100%).
 * Truyền dãy CHƯA cắt Top N.
 */
export function canDrawDonut(series: FlexibleGroupSeries, traits: FlexibleMetricTraits): boolean {
  if (!isMetricAdditive(traits)) return false
  if (series.drawableCount === 0 || series.drawableCount > DONUT_MAX_GROUPS) return false
  if (series.items.some((item) => item.value < 0)) return false
  return series.items.reduce((acc, item) => acc + item.value, 0) > 0
}

/** Câu ghi chú nhỏ dưới biểu đồ nhóm — rỗng khi không bỏ gì. */
export function describeSkippedGroups(series: FlexibleGroupSeries): string[] {
  const notes: string[] = []
  if (series.suppressedCount > 0) notes.push(`${series.suppressedCount} nhóm bị che không vẽ.`)
  if (series.zeroCount > 0) notes.push(`${series.zeroCount} nhóm bằng 0 không vẽ.`)
  if (series.skippedServerOther) notes.push('Phần "Các nhóm khác" máy chủ đã gộp sẵn không vẽ.')
  if (series.droppedRestCount > 0) {
    notes.push(
      `Còn ${series.droppedRestCount} nhóm nhỏ hơn không vẽ (chỉ số này không cộng gộp được).`,
    )
  }
  return notes
}

/** Câu hiện thay biểu đồ khi không có gì để vẽ — nói rõ VÌ SAO (chỉ có ở Tổng, bị che, chưa phát sinh). */
export function describeFlexibleChartEmpty(
  isTime: boolean,
  isSnapshot: boolean,
  series: FlexibleGroupSeries | null,
): string {
  if (isTime) {
    return isSnapshot
      ? 'Chỉ số này chỉ có ở Tổng — không vẽ được xu hướng theo kỳ.'
      : 'Kỳ này chưa có phát sinh.'
  }
  if (series?.metricMissing) return 'Chỉ số này chỉ có ở dòng Tổng — không chia theo nhóm được.'
  if (series && series.items.length === 0 && series.suppressedCount > 0) {
    return 'Mọi nhóm đều bị che — không có số để vẽ.'
  }
  return 'Chưa có nhóm nào có số để vẽ.'
}
