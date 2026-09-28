import { describe, expect, it } from 'vitest'

import { formatReportMetricValue } from './format-report-metric'

describe('formatReportMetricValue — null/undefined/NaN', () => {
  it('renders a dash, distinct from the number zero', () => {
    expect(formatReportMetricValue(null, 'int')).toBe('—')
    expect(formatReportMetricValue(undefined, 'money')).toBe('—')
    expect(formatReportMetricValue(Number.NaN, 'days')).toBe('—')
    expect(formatReportMetricValue(0, 'int')).toBe('0')
  })
})

describe('formatReportMetricValue — int', () => {
  it('groups thousands without a currency suffix', () => {
    expect(formatReportMetricValue(1234567, 'int')).toBe('1.234.567')
  })

  it('ignores the compact/full variant (there is nothing to shorten)', () => {
    expect(formatReportMetricValue(1234567, 'int', 'compact')).toBe('1.234.567')
  })
})

describe('formatReportMetricValue — money', () => {
  it('compact rút gọn tỷ/tr/k với dấu PHẨY thập phân — cùng quy ước với "74,5%" đứng cạnh', () => {
    expect(formatReportMetricValue(1_234_000_000, 'money', 'compact')).toBe('1,2 tỷ đ')
    expect(formatReportMetricValue(537_161_352, 'money', 'compact')).toBe('537,2 tr đ')
    expect(formatReportMetricValue(45_400, 'money', 'compact')).toBe('45 k đ')
    expect(formatReportMetricValue(-2_500_000, 'money', 'compact')).toBe('-2,5 tr đ')
  })

  it('full keeps every digit with the đ suffix', () => {
    expect(formatReportMetricValue(1_234_000_000, 'money', 'full')).toBe('1.234.000.000 đ')
  })

  it('rounds fractional đồng away instead of leaking cents (bug class fixed by shared format-money.ts)', () => {
    expect(formatReportMetricValue(4_760_000.08, 'money', 'full')).toBe('4.760.000 đ')
  })
})

describe('formatReportMetricValue — days', () => {
  it('keeps at most one decimal place', () => {
    expect(formatReportMetricValue(3.456, 'days')).toBe('3,5 ngày')
    expect(formatReportMetricValue(2, 'days')).toBe('2 ngày')
  })
})

describe('formatReportMetricValue — hours', () => {
  it('shows hours under a full day', () => {
    expect(formatReportMetricValue(5, 'hours')).toBe('5 giờ')
    expect(formatReportMetricValue(23.9, 'hours')).toBe('23,9 giờ')
  })

  it('switches to days once it reaches 24h, including the boundary itself', () => {
    expect(formatReportMetricValue(24, 'hours')).toBe('1 ngày')
    expect(formatReportMetricValue(60, 'hours')).toBe('2,5 ngày')
  })
})

describe('formatReportMetricValue — percent', () => {
  it('appends % and keeps up to two decimals', () => {
    expect(formatReportMetricValue(41.666, 'percent')).toBe('41,67%')
    expect(formatReportMetricValue(0, 'percent')).toBe('0%')
  })
})
