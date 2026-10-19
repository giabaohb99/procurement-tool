import type { UsageMetricKind } from '../config/usage-metric-labels'

const NONE = '—'

/** Phút-trong-ngày (0..1439) → «HH:MM». `null`/ngoài dải → «—». */
export function formatMinuteOfDay(minutes: number | null | undefined): string {
  if (minutes == null || !Number.isFinite(minutes) || minutes < 0 || minutes > 1439) return NONE
  const m = Math.round(minutes)
  return `${String(Math.floor(m / 60)).padStart(2, '0')}:${String(m % 60).padStart(2, '0')}`
}

/** Mili-giây → «6 phút 40 giây» / «2 giờ 5 phút» / «45 giây». */
export function formatDurationMs(ms: number | null | undefined): string {
  if (ms == null || !Number.isFinite(ms) || ms < 0) return NONE
  const totalSeconds = Math.round(ms / 1000)
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60
  if (hours > 0) return minutes > 0 ? `${hours} giờ ${minutes} phút` : `${hours} giờ`
  if (minutes > 0) return seconds > 0 ? `${minutes} phút ${seconds} giây` : `${minutes} phút`
  return `${seconds} giây`
}

/** Tỉ lệ 0..1 → «95%» (một số lẻ khi dưới 10%). */
export function formatRatio(ratio: number | null | undefined): string {
  if (ratio == null || !Number.isFinite(ratio)) return NONE
  const pct = ratio * 100
  return `${pct < 10 && pct !== 0 ? pct.toFixed(1).replace('.', ',') : Math.round(pct)}%`
}

export function formatCount(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return NONE
  return Number.isInteger(value) ? value.toLocaleString('vi-VN') : value.toFixed(1).replace('.', ',')
}

export function formatUsageValue(value: number | null | undefined, kind: UsageMetricKind): string {
  switch (kind) {
    case 'ratio':
      return formatRatio(value)
    case 'clock':
      return formatMinuteOfDay(value)
    case 'ms':
      return formatDurationMs(value)
    case 'minutes':
      return value == null ? '—' : `${formatCount(value)} phút`
    case 'hours':
      return value == null ? '—' : `${formatCount(value)} giờ`
    case 'per100':
      return value == null ? '—' : `${formatCount(value)}/100`
    default:
      return formatCount(value)
  }
}
