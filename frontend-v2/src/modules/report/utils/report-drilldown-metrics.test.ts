import { describe, expect, it } from 'vitest'

import type { ReportMeta, ReportMetricMeta } from '../types/report-analytics'
import { listDrilldownMetrics, pickDefaultDrilldownMetric } from './report-drilldown-metrics'

function metric(key: string, label: string): ReportMetricMeta {
  return { key, label, kind: 'int', good: null, helper: false, snapshot: false }
}

function meta(drilldown: string[] | undefined): ReportMeta {
  return {
    metrics: [metric('active', 'Đang hiệu lực'), metric('overdue', 'Đã quá hạn, vẫn đi làm')],
    dimensions: [],
    group_by: 'department',
    drilldown_metrics: drilldown,
  }
}

describe('listDrilldownMetrics', () => {
  it('returns nothing when an older server sends no drilldown_metrics', () => {
    expect(listDrilldownMetrics(meta(undefined))).toEqual([])
    expect(listDrilldownMetrics(meta([]))).toEqual([])
  })

  it('keeps backend order, labels from meta, and drops keys missing from meta.metrics', () => {
    //  `missing_id_number` bị backend gỡ khỏi `metrics` vì thiếu quyền nhạy cảm — không được
    //  hiện thành một lựa chọn trơ khóa kỹ thuật.
    expect(listDrilldownMetrics(meta(['overdue', 'missing_id_number', 'active', 'overdue']))).toEqual([
      { key: 'overdue', label: 'Đã quá hạn, vẫn đi làm' },
      { key: 'active', label: 'Đang hiệu lực' },
    ])
  })
})

describe('pickDefaultDrilldownMetric', () => {
  const options = [
    { key: 'active', label: 'A' },
    { key: 'overdue', label: 'B' },
  ]

  it('prefers the first preferred key that has a list', () => {
    expect(pickDefaultDrilldownMetric(options, ['complete_rate', 'overdue', 'active'])).toBe('overdue')
  })

  it('falls back to the first backend option, then to null', () => {
    expect(pickDefaultDrilldownMetric(options, ['complete_rate'])).toBe('active')
    expect(pickDefaultDrilldownMetric([], ['active'])).toBeNull()
  })
})
