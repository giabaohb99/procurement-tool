import type { UsageMetricBucket, UsageMetricTrendPoint } from '../types/usage-metric-catalog'
import { formatUsageValue } from './usage-format'
import { unitKind } from './usage-metric-catalog-helpers'

/** Dữ liệu một cột của biểu đồ phân phối. `label` ngắn cho trục X, `range` đầy đủ cho tooltip. */
export interface HistogramDatum {
  label: string
  range: string
  value: number
}

/** Dữ liệu một điểm của đường xu hướng. */
export interface TrendDatum {
  week: string
  label: string
  value: number | null
  measured: number
}

const fmt = (v: number, unit: string) => formatUsageValue(v, unitKind(unit))

/** Nhãn ngắn trên trục X: cận dưới của cột (cột tràn có "≥"; cờ 0/1 hiện "Không"/"Có"). */
export function bucketAxisLabel(b: UsageMetricBucket, unit: string): string {
  if (unit === 'flag') return b.lo >= 1 ? 'Có' : 'Không'
  return b.hi === null ? `≥${fmt(b.lo, unit)}` : fmt(b.lo, unit)
}

/** Khoảng đầy đủ của cột. Cột là nửa mở nên cận trên của giờ/số đếm được lùi 1 đơn vị để khỏi đọc nhầm. */
export function bucketRangeText(b: UsageMetricBucket, unit: string): string {
  if (unit === 'flag') return b.lo >= 1 ? 'Có' : 'Không'
  if (b.hi === null) return `≥ ${fmt(b.lo, unit)}`
  if (unit === 'minute_of_day') return `${fmt(b.lo, unit)} – ${fmt(b.hi - 1, unit)}`
  if (unit === 'count') return b.hi - b.lo <= 1 ? fmt(b.lo, unit) : `${fmt(b.lo, unit)} – ${fmt(b.hi - 1, unit)}`
  return `${fmt(b.lo, unit)} – ${fmt(b.hi, unit)}`
}

export function buildHistogramData(buckets: UsageMetricBucket[], unit: string): HistogramDatum[] {
  return buckets.map((b) => ({ label: bucketAxisLabel(b, unit), range: bucketRangeText(b, unit), value: b.count }))
}

/** Chỉ số cột chứa trung vị (để vẽ vạch đứng); -1 nếu không có. Trung vị 100% rơi vào cột cuối. */
export function medianBucketIndex(buckets: UsageMetricBucket[], median: number | null): number {
  if (median == null || buckets.length === 0) return -1
  const idx = buckets.findIndex((b) => median >= b.lo && (b.hi === null || median < b.hi))
  return idx >= 0 ? idx : median >= buckets[buckets.length - 1].lo ? buckets.length - 1 : -1
}

/** "2026-10-12" → "12/10". Chuỗi lạ giữ nguyên. */
export function weekShortLabel(iso: string): string {
  const m = /^\d{4}-(\d{2})-(\d{2})/.exec(iso)
  return m ? `${m[2]}/${m[1]}` : iso
}

export function buildTrendData(points: UsageMetricTrendPoint[]): TrendDatum[] {
  return points.map((p) => ({ week: p.week, label: weekShortLabel(p.week), value: p.median, measured: p.measured }))
}
