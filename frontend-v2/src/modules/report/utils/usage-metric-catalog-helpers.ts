import type { UsageMetricKind } from '../config/usage-metric-labels'

/** Đơn vị backend (`metric_catalog.py`) → cách định dạng ở lớp hiển thị. `flag` (0/1) hiện như số đếm. */
const UNIT_KIND: Record<string, UsageMetricKind> = {
  ratio: 'ratio', count: 'count', min: 'minutes', h: 'hours', ms: 'ms', per100: 'per100',
  minute_of_day: 'clock', flag: 'count',
}

export function unitKind(unit: string): UsageMetricKind {
  return UNIT_KIND[unit] ?? 'count'
}

/** «Tốt khi» theo `direction` backend: 1 cao · -1 thấp · 0 không phán xét. */
export function goodWhenLabel(direction: number): string {
  return direction > 0 ? 'Cao' : direction < 0 ? 'Thấp' : 'Không phán xét'
}

/** Chữ trạng thái khi chỉ số CHƯA có người đo (mã `UnmeasuredReason`: 1 chưa thu thập · 2 chưa đủ dữ liệu · 3 không áp dụng). */
export function unmeasuredStatusText(hasWeek: boolean, reason: number | null): string | null {
  if (!hasWeek) return 'Chưa thu thập'
  return reason === 2 ? 'Chưa đủ dữ liệu' : reason === 3 ? 'Không áp dụng' : reason === 1 ? 'Chưa thu thập' : null
}
