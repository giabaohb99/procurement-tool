import type { ReportFiltersState } from '../hooks/use-report-filters'
import type { useReportDrilldownState } from '../hooks/use-report-drilldown-state'
import type {
  ReportAnalyticsResponse,
  ReportMetricValues,
  ReportPageConfig,
} from '../types/report-analytics'
import { ReportBreakdownCharts } from './report-breakdown-charts'
import { ReportGroupedTable } from './report-grouped-table'
import { ReportKpiRow } from './report-kpi-row'
import { ReportNotes } from './report-notes'
import { ReportPeriodEmptyState } from './report-period-empty-state'
import { ReportTrendChart } from './report-trend-chart'

const EMPTY_METRICS: ReportMetricValues = {}

interface ReportAnalyticsBodyProps {
  config: ReportPageConfig
  data: ReportAnalyticsResponse | undefined
  isLoading: boolean
  filters: ReportFiltersState
  chartMetric: string
  onChartMetricChange: (metric: string) => void
  drilldown: ReturnType<typeof useReportDrilldownState>
}

/**
 * Thân trang báo cáo Haravan khi KHÔNG lỗi: lưu ý cách tính → thẻ KPI → biểu đồ xu hướng
 * (trừ `hideTrend`) → breakdown phụ → bảng «Xem theo». Kỳ trống thay ba khối sau cùng
 * bằng MỘT thông báo — trừ trang `hidePeriod` (tình trạng hiện tại, không có "kỳ trống").
 */
export function ReportAnalyticsBody({
  config,
  data,
  isLoading,
  filters,
  chartMetric,
  onChartMetricChange,
  drilldown,
}: ReportAnalyticsBodyProps) {
  const meta = data?.meta ?? { metrics: [], dimensions: [], group_by: config.defaultGroupBy }
  const totals = data?.totals ?? { current: EMPTY_METRICS, compare: null }
  const trend = data?.trend ?? []
  //  Kỳ không phát sinh gì: mọi chỉ số THEO KỲ ở dòng Tổng bằng 0/`null`. Bỏ qua
  //  chỉ số `snapshot` (công nợ còn lại…) — số dư vẫn còn dù kỳ này chẳng mua gì.
  const isPeriodEmpty =
    !config.hidePeriod &&
    !!data &&
    meta.metrics.filter((m) => !m.snapshot).every((m) => !totals.current[m.key])

  return (
    <>
      {/*  `notes` mang các lưu ý tính toán quan trọng — backend là nguồn DUY NHẤT,
           tầng này hiện nguyên văn (gấp sẵn, bấm để mở). */}
      <ReportNotes notes={data?.notes ?? []} />

      <ReportKpiRow
        meta={meta}
        kpis={config.kpis}
        totals={totals}
        trend={trend}
        compareMode={filters.compare}
        selectedMetric={chartMetric}
        //  Không có biểu đồ thì bấm thẻ chẳng đổi được gì — thẻ tĩnh.
        onSelectMetric={config.hideTrend ? undefined : onChartMetricChange}
        isLoading={isLoading}
        drilldownMetrics={drilldown.metricKeys}
        onDrilldown={drilldown.enabled ? drilldown.openMetric : undefined}
      />

      {isPeriodEmpty ? (
        <ReportPeriodEmptyState
          period={data?.period}
          onViewFullYear={() =>
            filters.applyPeriod({ preset: 'this_year', from: '', to: '', compare: filters.compare })
          }
        />
      ) : (
        <>
          {!config.hideTrend && (
            <ReportTrendChart
              meta={meta}
              trend={trend}
              metric={chartMetric}
              compareMode={filters.compare}
              isLoading={isLoading}
            />
          )}

          {config.breakdowns && config.breakdowns.length > 0 && (
            <ReportBreakdownCharts
              breakdowns={data?.breakdowns}
              meta={data?.meta}
              config={config.breakdowns}
              isLoading={isLoading}
            />
          )}

          <ReportGroupedTable
            meta={meta}
            kpis={config.kpis}
            totals={totals}
            groups={data?.groups ?? []}
            compare={filters.compare}
            groupBy={filters.groupBy}
            onGroupByChange={filters.setGroupBy}
            isLoading={isLoading}
            isError={false}
            //  `.v4` — mặc định chỉ hiện cột `kpis`, còn lại `defaultHidden`
            //  (`docs/ui/table.md` §4: đổi mặc định cột thì phải đổi khóa mới).
            storageKey={`report.${config.slug}.v4`}
            onDrilldownRow={drilldown.enabled ? drilldown.openRow : undefined}
          />
        </>
      )}
    </>
  )
}
