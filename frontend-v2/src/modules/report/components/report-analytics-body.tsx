import { useMemo } from 'react'

import type { ReportFiltersState } from '../hooks/use-report-filters'
import type { useReportDrilldownState } from '../hooks/use-report-drilldown-state'
import type {
  ReportAnalyticsResponse,
  ReportMetricValues,
  ReportPageConfig,
} from '../types/report-analytics'
import { ReportBreakdownCharts } from './report-breakdown-charts'
import { ReportFlexibleChart } from './report-flexible-chart'
import { ReportGroupedTable } from './report-grouped-table'
import { ReportKpiRow } from './report-kpi-row'
import { ReportNotes } from './report-notes'
import { ReportPeriodEmptyState } from './report-period-empty-state'

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
  const tableColumns = useMemo(
    () => [...config.kpis, ...(config.tableMetrics ?? [])],
    [config.kpis, config.tableMetrics],
  )
  //  Bấm cột/lát → ngăn «Danh sách» của nhóm đó, chỉ khi chỉ số đang vẽ có danh sách. Chặn thêm
  //  lúc `meta.group_by` (số đang hiện, `keepPreviousData`) còn lệch «Xem theo» vừa đổi — không
  //  thì mở danh sách với chiều MỚI nhưng khóa nhóm của chiều CŨ.
  const canDrillGroup =
    drilldown.enabled && drilldown.metricKeys.has(chartMetric) && meta.group_by === filters.groupBy
  const openGroupDrilldown = (group: { key: string; label: string }) =>
    drilldown.openRow({
      ...group,
      current: {},
      compare: null,
      isTotal: false,
      isEmpty: false,
      isSuppressed: false,
    })
  //  Chỉ số thời điểm mà nhóm có số (vd «Định biên cuối kỳ» theo phòng ban) — thẻ KPI của nó
  //  bấm được để biểu đồ linh hoạt vẽ theo nhóm (duoc-CR-688).
  const groupedSnapshotMetrics = useMemo(
    () =>
      new Set(
        meta.metrics
          .filter((m) => m.snapshot)
          .filter((m) => (data?.groups ?? []).some((g) => typeof g.current[m.key] === 'number'))
          .map((m) => m.key),
      ),
    [meta.metrics, data?.groups],
  )
  //  Kỳ không phát sinh gì: mọi chỉ số THEO KỲ ở dòng Tổng bằng 0/`null`. Bỏ qua
  //  chỉ số `snapshot` (công nợ còn lại…) — số dư vẫn còn dù kỳ này chẳng mua gì.
  //  duoc-CR-688: nhóm còn mang số thời điểm (vd «Định biên cuối kỳ» theo phòng ban) thì kỳ
  //  KHÔNG trống — tháng không ai vào/nghỉ vẫn phải xem được quân số từng phòng.
  const isPeriodEmpty =
    !config.hidePeriod &&
    !!data &&
    groupedSnapshotMetrics.size === 0 &&
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
        //  Biểu đồ linh hoạt có mặt ở MỌI trang (trang `hideTrend` vẽ theo nhóm) nên thẻ luôn bấm được.
        onSelectMetric={onChartMetricChange}
        isLoading={isLoading}
        drilldownMetrics={drilldown.metricKeys}
        onDrilldown={drilldown.enabled ? drilldown.openMetric : undefined}
        groupedSnapshotMetrics={groupedSnapshotMetrics}
      />

      {config.kpiNotice && data && <config.kpiNotice meta={data.meta} />}

      {isPeriodEmpty ? (
        <ReportPeriodEmptyState
          period={data?.period}
          onViewFullYear={() =>
            filters.applyPeriod({ preset: 'this_year', from: '', to: '', compare: filters.compare })
          }
        />
      ) : (
        <>
          <ReportFlexibleChart
            slug={config.slug}
            hideTrend={config.hideTrend}
            meta={meta}
            trend={trend}
            groups={data?.groups ?? []}
            period={data?.period}
            metric={chartMetric}
            compareMode={filters.compare}
            isLoading={isLoading}
            onSelectGroup={canDrillGroup ? openGroupDrilldown : undefined}
          />

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
            //  Cột hiện sẵn = thẻ KPI rồi tới `tableMetrics` (cùng thứ tự đó).
            kpis={tableColumns}
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
