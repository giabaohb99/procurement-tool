import { describe, expect, it } from 'vitest'

import type { ReportMetricMeta } from '../types/report-analytics'
import { orderVisibleReportMetrics } from './order-visible-report-metrics'

function metric(key: string, overrides: Partial<ReportMetricMeta> = {}): ReportMetricMeta {
  return { key, label: key, kind: 'int', good: null, helper: false, snapshot: false, ...overrides }
}

describe('orderVisibleReportMetrics — helper metrics never appear', () => {
  it('drops every metric flagged helper regardless of position', () => {
    const metrics = [metric('a'), metric('b', { helper: true }), metric('c')]
    const result = orderVisibleReportMetrics(metrics, [])
    expect(result.map((m) => m.key)).toEqual(['a', 'c'])
  })

  it('drops a helper metric even when it is (mistakenly) listed in kpis', () => {
    const metrics = [metric('a'), metric('b', { helper: true })]
    const result = orderVisibleReportMetrics(metrics, ['b', 'a'])
    expect(result.map((m) => m.key)).toEqual(['a'])
  })
})

describe('orderVisibleReportMetrics — kpis come first, in the configured order', () => {
  it('reorders so kpis lead even when they appear later in meta.metrics', () => {
    const metrics = [metric('extra1'), metric('amount'), metric('extra2'), metric('lines')]
    const result = orderVisibleReportMetrics(metrics, ['lines', 'amount'])
    expect(result.map((m) => m.key)).toEqual(['lines', 'amount', 'extra1', 'extra2'])
  })

  it('keeps the remaining (non-kpi) metrics in their original meta.metrics order', () => {
    const metrics = [metric('z'), metric('y'), metric('x')]
    const result = orderVisibleReportMetrics(metrics, [])
    expect(result.map((m) => m.key)).toEqual(['z', 'y', 'x'])
  })

  it('ignores a kpi key backend never sent, instead of throwing or inserting a hole', () => {
    const metrics = [metric('amount')]
    const result = orderVisibleReportMetrics(metrics, ['does_not_exist', 'amount'])
    expect(result.map((m) => m.key)).toEqual(['amount'])
  })

  it('handles an empty metrics list without throwing', () => {
    expect(orderVisibleReportMetrics([], ['amount'])).toEqual([])
  })
})
