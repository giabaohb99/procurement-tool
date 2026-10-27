import { useCallback, useMemo, useState } from 'react'

import type { ReportMeta } from '../types/report-analytics'
import type { ReportDrilldownTarget } from '../types/report-drilldown'
import type { ReportTableRow } from '../utils/build-report-table-rows'
import { listDrilldownMetrics, pickDefaultDrilldownMetric } from '../utils/report-drilldown-metrics'

interface UseReportDrilldownStateInput {
  /** `ReportPageConfig.drilldownEndpoint` — bỏ trống thì trang không có danh sách nào. */
  endpoint: string | undefined
  meta: ReportMeta
  /** Chiều «Xem theo» đang chọn — thành `group_by` khi mở danh sách từ một dòng nhóm. */
  groupBy: string
  /** Thứ tự ưu tiên chọn chỉ số khi mở từ dòng nhóm: chỉ số biểu đồ, rồi thẻ KPI. */
  preferredMetrics: string[]
}

/**
 * Trạng thái ngăn «Danh sách người» của một trang báo cáo (duoc-CR-686): chỉ số nào bấm
 * được, đang mở chỉ số/nhóm nào. Trang không khai `drilldownEndpoint` hoặc backend không
 * trả `drilldown_metrics` → `metricOptions` rỗng, mọi nút «Xem danh sách» tự biến mất.
 */
export function useReportDrilldownState({
  endpoint,
  meta,
  groupBy,
  preferredMetrics,
}: UseReportDrilldownStateInput) {
  const [target, setTarget] = useState<ReportDrilldownTarget | null>(null)

  const metricOptions = useMemo(() => (endpoint ? listDrilldownMetrics(meta) : []), [endpoint, meta])
  const metricKeys = useMemo(() => new Set(metricOptions.map((o) => o.key)), [metricOptions])
  const dimensionLabel = meta.dimensions.find((d) => d.key === groupBy)?.label ?? 'Nhóm'
  const defaultMetric = pickDefaultDrilldownMetric(metricOptions, preferredMetrics)

  const openMetric = useCallback((metric: string) => setTarget({ metric, group: null }), [])

  const openRow = useCallback(
    (row: ReportTableRow) => {
      if (!defaultMetric) return
      setTarget({
        metric: defaultMetric,
        group: row.isTotal ? null : { by: groupBy, key: row.key, dimensionLabel, label: row.label },
      })
    },
    [defaultMetric, groupBy, dimensionLabel],
  )

  const changeMetric = useCallback(
    (metric: string) => setTarget((t) => (t ? { ...t, metric } : t)),
    [],
  )
  const close = useCallback(() => setTarget(null), [])

  return {
    enabled: metricOptions.length > 0,
    metricOptions,
    metricKeys,
    target,
    openMetric,
    openRow,
    changeMetric,
    close,
  }
}
