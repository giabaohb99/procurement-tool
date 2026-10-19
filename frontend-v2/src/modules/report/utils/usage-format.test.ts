import { describe, expect, it } from 'vitest'

import { formatCount, formatDurationMs, formatMinuteOfDay, formatRatio, formatUsageValue } from './usage-format'

describe('usage-format', () => {
  it('formats minute-of-day as HH:MM and rejects out-of-range values', () => {
    expect(formatMinuteOfDay(0)).toBe('00:00')
    expect(formatMinuteOfDay(1439)).toBe('23:59')
    expect(formatMinuteOfDay(485)).toBe('08:05')
    expect(formatMinuteOfDay(1440)).toBe('—')
    expect(formatMinuteOfDay(-1)).toBe('—')
    expect(formatMinuteOfDay(null)).toBe('—')
    expect(formatMinuteOfDay(Number.NaN)).toBe('—')
  })

  it('formats durations in Vietnamese units', () => {
    expect(formatDurationMs(400000)).toBe('6 phút 40 giây')
    expect(formatDurationMs(45_000)).toBe('45 giây')
    expect(formatDurationMs(7_500_000)).toBe('2 giờ 5 phút')
    expect(formatDurationMs(3_600_000)).toBe('1 giờ')
    expect(formatDurationMs(0)).toBe('0 giây')
    expect(formatDurationMs(null)).toBe('—')
    expect(formatDurationMs(-5)).toBe('—')
  })

  it('formats ratios and keeps 0 distinct from missing', () => {
    expect(formatRatio(0.95)).toBe('95%')
    expect(formatRatio(0.045)).toBe('4,5%')
    expect(formatRatio(0)).toBe('0%')
    expect(formatRatio(null)).toBe('—')
    expect(formatRatio(undefined)).toBe('—')
  })

  it('formats counts', () => {
    expect(formatCount(0)).toBe('0')
    expect(formatCount(2.5)).toBe('2,5')
    expect(formatCount(null)).toBe('—')
  })
})

describe('formatUsageValue', () => {
  it('formats by metric kind', () => {
    expect(formatUsageValue(0.5, 'ratio')).toBe('50%')
    expect(formatUsageValue(485, 'clock')).toBe('08:05')
    expect(formatUsageValue(400000, 'ms')).toBe('6 phút 40 giây')
    expect(formatUsageValue(12, 'minutes')).toBe('12 phút')
    expect(formatUsageValue(6, 'hours')).toBe('6 giờ')
    expect(formatUsageValue(4, 'per100')).toBe('4/100')
    expect(formatUsageValue(3, 'count')).toBe('3')
    expect(formatUsageValue(null, 'hours')).toBe('—')
  })
})
