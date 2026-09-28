import { useMemo } from 'react'

import { ChartCard } from '@/shared/ui/chart'

import { formatReportMetricValue } from '../utils/format-report-metric'
import type { ReportCompareMode, ReportMeta, ReportTrendPoint } from '../types/report-analytics'
import { PeriodComparisonChart } from './period-comparison-chart'

interface ReportTrendChartProps {
  meta: ReportMeta
  trend: ReportTrendPoint[]
  /** Chỉ số đang chọn — đổi bằng cách bấm một thẻ trong `ReportKpiRow`. */
  metric: string
  compareMode: ReportCompareMode
  isLoading: boolean
}

const COMPARE_CHART_LABEL: Record<ReportCompareMode, string> = {
  previous: 'Kỳ trước',
  year: 'Cùng kỳ năm trước',
  none: 'Kỳ trước',
}

/**
 * Biểu đồ xu hướng kỳ này vs kỳ so sánh — khối trung tâm của trang báo cáo
 * Haravan. Vẽ đúng MỘT chỉ số tại một thời điểm (`metric`), đổi bằng cách bấm
 * thẻ KPI phía trên; trục thời gian và số mốc do backend quyết định
 * (`period.granularity`), tầng này chỉ đọc `trend[].label` có sẵn.
 */
export function ReportTrendChart({
  meta,
  trend,
  metric,
  compareMode,
  isLoading,
}: ReportTrendChartProps) {
  const metricMeta = meta.metrics.find((m) => m.key === metric)

  const data = useMemo(
    () =>
      trend.map((point) => ({
        label: point.label,
        current: point.current[metric] ?? null,
        previous: compareMode === 'none' ? null : (point.compare?.[metric] ?? null),
      })),
    [trend, metric, compareMode],
  )

  //  `snapshot` (vd công nợ) không có mặt trong `trend[]` — mọi mốc rỗng, KHÔNG
  //  phải "chưa phát sinh". Chặn phòng khi `chartMetric` cấu hình lỡ trỏ vào một
  //  chỉ số snapshot (UI bình thường đã chặn bấm chọn nó ở `ReportKpiRow`).
  const isSnapshot = metricMeta?.snapshot ?? false
  const isEmpty = isSnapshot || data.every((p) => (p.current ?? 0) === 0 && (p.previous ?? 0) === 0)

  return (
    <ChartCard
      title={metricMeta ? `Xu hướng ${metricMeta.label}` : 'Xu hướng'}
      description="Bấm vào một thẻ chỉ số phía trên để đổi chỉ số đang xem."
      loading={isLoading}
      isEmpty={isEmpty}
      emptyLabel={
        isSnapshot
          ? 'Chỉ số này chỉ có ở Tổng — không vẽ được xu hướng theo kỳ.'
          : 'Kỳ này chưa có phát sinh.'
      }
    >
      <PeriodComparisonChart
        data={data}
        currentLabel="Kỳ này"
        previousLabel={COMPARE_CHART_LABEL[compareMode]}
        allowDecimals={metricMeta?.kind !== 'int'}
        formatValue={(value) =>
          formatReportMetricValue(value, metricMeta?.kind ?? 'int', 'compact')
        }
      />
    </ChartCard>
  )
}
