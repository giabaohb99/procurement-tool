import { ChartCard, CHART_NEUTRAL } from '@/shared/ui/chart'

import { useReportFlexibleChartOptions } from '../hooks/use-report-flexible-chart-options'
import { useReportFlexibleChartPngDownload } from '../hooks/use-report-flexible-chart-png-download'
import type {
  ReportCompareMode,
  ReportGroupRow,
  ReportMeta,
  ReportPeriod,
  ReportTrendPoint,
} from '../types/report-analytics'
import { formatReportMetricValue } from '../utils/format-report-metric'
import { formatReportRange } from '../utils/format-report-range'
import { pickDonutColor } from '../utils/report-flexible-chart-colors'
import { parseChartTop } from '../utils/report-flexible-chart-options'
import { buildChartPngFilename } from '../utils/report-flexible-chart-png'
import {
  buildFlexibleGroupSeries,
  buildFlexibleTimeSeries,
  canDrawDonut,
  describeFlexibleChartEmpty,
  describeSkippedGroups,
  type FlexibleGroupItem,
} from '../utils/report-flexible-chart-series'
import { PeriodComparisonChart } from './period-comparison-chart'
import { ReportFlexibleChartDonut } from './report-flexible-chart-donut'
import { ReportFlexibleChartGroupBars } from './report-flexible-chart-group-bars'
import { ReportFlexibleChartTimeBars } from './report-flexible-chart-time-bars'
import { ReportFlexibleChartToolbar } from './report-flexible-chart-toolbar'

const COMPARE_CHART_LABEL: Record<ReportCompareMode, string> = {
  previous: 'Kỳ trước',
  year: 'Cùng kỳ năm trước',
  none: 'Kỳ trước',
}
const METRIC_HINT = 'Bấm vào một thẻ chỉ số phía trên để đổi chỉ số đang xem.'

interface ReportFlexibleChartProps {
  /** `ReportPageConfig.slug` — tên tệp ảnh `bieu-do-<slug>-<từ>-<đến>.png`. */
  slug: string
  /** `ReportPageConfig.hideTrend` — báo cáo không có trục thời gian: chỉ vẽ theo nhóm. */
  hideTrend?: boolean
  meta: ReportMeta
  trend: ReportTrendPoint[]
  groups: ReportGroupRow[]
  period?: ReportPeriod
  /** Chỉ số đang chọn — đổi bằng cách bấm một thẻ KPI. */
  metric: string
  compareMode: ReportCompareMode
  isLoading: boolean
  /** Bấm một cột / một lát của nhóm thật → mở ngăn "Danh sách". Bỏ trống = không bấm được. */
  onSelectGroup?: (group: { key: string; label: string }) => void
}

/**
 * "Biểu đồ linh hoạt" (duoc-CR-688, §3.4 của `doc/erp/hrm/05-bao-cao-nhan-su.md`) — thay khối
 * xu hướng cố định của mọi trang `ReportAnalyticsPage`. MẶC ĐỊNH trông y như cũ (đường xu hướng
 * chỉ số đang chọn, kèm kỳ so sánh); người xem đổi "Vẽ theo" thời gian / chiều "Xem theo", kiểu
 * biểu đồ và Top N — ba lựa chọn nằm trên URL.
 */
export function ReportFlexibleChart({
  slug,
  hideTrend = false,
  meta,
  trend,
  groups,
  period,
  metric,
  compareMode,
  isLoading,
  onSelectGroup,
}: ReportFlexibleChartProps) {
  const { plotRef, downloading, download } = useReportFlexibleChartPngDownload()
  const metricMeta = meta.metrics.find((m) => m.key === metric)
  const kind = metricMeta?.kind ?? 'int'
  const traits = { kind, additive: metricMeta?.additive }
  const isSnapshot = metricMeta?.snapshot ?? false
  const groupLabel =
    meta.group_by && meta.group_by !== 'none'
      ? (meta.dimensions.find((d) => d.key === meta.group_by)?.label ?? null)
      : null

  //  Đang tải lần đầu (`trend` rỗng vì CHƯA có số) thì vẫn coi như có trục thời gian — khỏi
  //  nháy sang "theo nhóm" rồi nháy về khi số về.
  //  Trục thời gian chỉ khi `trend` thật sự MANG chỉ số này (chỉ số thời điểm, hay chỉ số máy
  //  chủ bỏ khỏi `trend`, thì vắng khóa ở mọi mốc — vẽ ra chỉ là một đường số 0 giả).
  const trendHasMetric = trend.some((point) => metric in point.current)
  const hasTime = !hideTrend && !isSnapshot && (isLoading || trendHasMetric)
  //  Vành khuyên xét trên dãy CHƯA cắt Top N — đổi Top không được làm mất lựa chọn vành khuyên.
  const fullSeries = buildFlexibleGroupSeries(groups, metric, null, traits)
  const donutAllowed = canDrawDonut(fullSeries, traits)
  const { options, setOptions } = useReportFlexibleChartOptions({
    hasTime,
    hasGroup: groupLabel !== null,
    preferGroup: hideTrend || isSnapshot,
    donutAllowed,
  })

  const formatValue = (value: number) => formatReportMetricValue(value, kind, 'compact')
  const metricLabel = metricMeta?.label ?? ''
  const isTime = options.by === 'time'
  const title = isTime
    ? metricLabel
      ? `Xu hướng ${metricLabel}`
      : 'Xu hướng'
    : `${metricLabel || 'Chỉ số'} theo ${groupLabel ?? 'nhóm'}`

  //  ---- Thời gian: y hệt `ReportTrendChart` cũ ----
  const timeData = buildFlexibleTimeSeries(trend, metric, compareMode)
  const integerAxis = kind === 'int' || kind === 'days'
  const maxValue = Math.max(0, ...timeData.map((p) => Math.max(p.current ?? 0, p.previous ?? 0)))
  const tickCount = integerAxis && maxValue < 4 ? Math.max(2, Math.ceil(maxValue) + 1) : undefined
  const timeEmpty =
    isSnapshot || timeData.every((p) => (p.current ?? 0) === 0 && (p.previous ?? 0) === 0)

  //  ---- Nhóm ----
  const series = isTime ? null : buildFlexibleGroupSeries(groups, metric, parseChartTop(options.top), traits)
  const groupEmpty = !series || series.items.length === 0
  const selectItem = onSelectGroup
    ? (item: FlexibleGroupItem) => onSelectGroup({ key: item.key, label: item.label })
    : undefined

  const emptyLabel = describeFlexibleChartEmpty(isTime, isSnapshot, series)
  const isEmpty = isTime ? timeEmpty : groupEmpty
  const showPrevious = compareMode !== 'none'
  const notes = series ? describeSkippedGroups(series) : []

  const handleDownload = () => {
    const legend =
      isTime && showPrevious
        ? [
            { label: 'Kỳ này', color: 'var(--chart-1)' },
            { label: COMPARE_CHART_LABEL[compareMode], color: CHART_NEUTRAL },
          ]
        : options.type === 'donut' && series
          ? series.items.map((item, i) => ({
              label: `${item.label}: ${formatValue(item.value)}`,
              color: pickDonutColor(item, i),
            }))
          : []
    void download({
      filename: buildChartPngFilename(slug, period),
      title: period ? `${title} · ${formatReportRange(period.date_from, period.date_to)}` : title,
      legend,
    })
  }

  return (
    <ChartCard
      title={title}
      description={
        !isTime && selectItem ? 'Bấm vào một nhóm trên biểu đồ để xem danh sách người của nhóm đó.' : METRIC_HINT
      }
      loading={isLoading}
    >
      <div className="flex flex-col gap-3">
        <ReportFlexibleChartToolbar
          options={options}
          hasTime={hasTime}
          groupLabel={groupLabel}
          donutAllowed={donutAllowed}
          onChange={setOptions}
          onDownload={handleDownload}
          downloadDisabled={isEmpty || downloading}
        />
        {isEmpty ? (
          <p className="py-8 text-center text-sm text-muted-foreground">{emptyLabel}</p>
        ) : (
          <figure ref={plotRef} aria-label={title} className="m-0 min-w-0">
            {isTime && options.type === 'line' && (
              <PeriodComparisonChart
                data={timeData}
                currentLabel="Kỳ này"
                previousLabel={COMPARE_CHART_LABEL[compareMode]}
                allowDecimals={!integerAxis}
                tickCount={tickCount}
                formatValue={formatValue}
              />
            )}
            {isTime && options.type === 'bar' && (
              <ReportFlexibleChartTimeBars
                data={timeData}
                currentLabel="Kỳ này"
                previousLabel={COMPARE_CHART_LABEL[compareMode]}
                showPrevious={showPrevious}
                allowDecimals={!integerAxis}
                tickCount={tickCount}
                formatValue={formatValue}
              />
            )}
            {series && (options.type === 'hbar' || options.type === 'bar') && (
              <ReportFlexibleChartGroupBars
                items={series.items}
                orientation={options.type === 'hbar' ? 'horizontal' : 'vertical'}
                formatValue={formatValue}
                onSelectItem={selectItem}
              />
            )}
            {series && options.type === 'donut' && (
              <ReportFlexibleChartDonut
                items={series.items}
                formatValue={formatValue}
                onSelectItem={selectItem}
              />
            )}
          </figure>
        )}
        {!isEmpty && notes.length > 0 && (
          <p className="text-xs text-muted-foreground">{notes.join(' ')}</p>
        )}
      </div>
    </ChartCard>
  )
}
