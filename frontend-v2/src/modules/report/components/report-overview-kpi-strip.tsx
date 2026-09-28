import { cn } from '@/shared/utils/cn'
import { formatReportMetricValue } from '../utils/format-report-metric'
import { compareCaption, describeMetricChange } from '../utils/report-period-comparison'
import { kpiGridColumnsClass } from '../utils/kpi-grid-columns'
import type { ReportCompareMode, ReportMetricKind } from '../types/report-analytics'
import type { ReportOverviewEntry } from '../hooks/use-report-overview'
import { KpiTrendCard } from './kpi-trend-card'

/** Chỉ số ĐANG chọn để vẽ trên biểu đồ xu hướng chính của trang Tổng quan. */
export interface OverviewMetricSelection {
  /** `ReportCatalogEntry.endpoint` của báo cáo sở hữu chỉ số này. */
  endpoint: string
  metric: string
  label: string
  kind: ReportMetricKind
}

interface ReportOverviewKpiStripProps {
  entries: ReportOverviewEntry[]
  compareMode: ReportCompareMode
  selected: OverviewMetricSelection | null
  onSelect: (selection: OverviewMetricSelection) => void
}

/**
 * Dải "Chỉ số chính" của trang Tổng quan — mỗi báo cáo góp 1–2 mini-KPI
 * (`ReportCatalogEntry.overviewKpis`), gom theo PHÂN HỆ (`report.group`). Bấm
 * một thẻ để đổi biểu đồ xu hướng chính (`ReportOverviewPage`) sang chỉ số đó;
 * `hint` luôn hiện TÊN BÁO CÁO vì hai báo cáo khác nhau có thể trùng nhãn chỉ
 * số (vd "Giao đúng hạn" của cả Báo cáo mua hàng lẫn Tiến độ mua hàng).
 */
export function ReportOverviewKpiStrip({
  entries,
  compareMode,
  selected,
  onSelect,
}: ReportOverviewKpiStripProps) {
  if (entries.length === 0) return null

  const groups = new Map<string, ReportOverviewEntry[]>()
  for (const entry of entries) {
    groups.set(entry.report.group, [...(groups.get(entry.report.group) ?? []), entry])
  }

  return (
    <div className="flex flex-col gap-4">
      {[...groups].map(([group, groupEntries]) => (
        <section key={group} className="flex flex-col gap-2">
          <h3 className="text-sm font-semibold text-muted-foreground">{group}</h3>
          <div
            className={cn(
              'grid grid-cols-2 gap-3 sm:gap-4',
              kpiGridColumnsClass(
                groupEntries.reduce((n, e) => n + e.report.overviewKpis.length, 0),
              ),
            )}
          >
            {groupEntries.flatMap((entry) =>
              //  `flatMap` (không `map`) để chỉ số `helper` — vô nghĩa đứng
              //  riêng — bỏ hẳn khỏi dải, không phải hiện thẻ rỗng cho nó.
              entry.report.overviewKpis.flatMap((metricKey) => {
                const metric = entry.data?.meta.metrics.find((m) => m.key === metricKey)
                if (metric?.helper) return []

                //  `?? null`, KHÔNG `?? 0` — chỉ số dẫn xuất mẫu số 0 phải ra
                //  "—", không phải "0" (khác giá trị THẬT bằng 0).
                const current = entry.data?.totals.current[metricKey] ?? null
                const compareValue = entry.data?.totals.compare?.[metricKey] ?? null
                const changeDescription =
                  compareMode === 'none' || !metric
                    ? undefined
                    : describeMetricChange(current, compareValue, metric.kind, metric.good)
                const isSelected =
                  selected?.endpoint === entry.report.endpoint && selected.metric === metricKey

                return [
                  <KpiTrendCard
                    key={`${entry.report.path}__${metricKey}`}
                    label={metric?.label ?? entry.report.label}
                    value={metric ? formatReportMetricValue(current, metric.kind, 'compact') : '—'}
                    changeDescription={changeDescription}
                    changeCaption={compareMode === 'none' ? undefined : compareCaption(compareMode)}
                    hint={entry.report.label}
                    loading={entry.isLoading && !entry.data}
                    selected={isSelected}
                    //  `snapshot`: không có xu hướng theo kỳ để vẽ — chọn nó làm
                    //  chỉ số đang xem của biểu đồ bên dưới chỉ ra một khối rỗng.
                    onClick={
                      metric && !metric.snapshot
                        ? () =>
                            onSelect({
                              endpoint: entry.report.endpoint,
                              metric: metricKey,
                              label: metric.label,
                              kind: metric.kind,
                            })
                        : undefined
                    }
                  />,
                ]
              }),
            )}
          </div>
        </section>
      ))}
    </div>
  )
}
