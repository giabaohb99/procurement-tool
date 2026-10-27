import { List } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'
import { Skeleton } from '@/shared/ui/skeleton'

import { formatReportMetricValue } from '../utils/format-report-metric'
import { compareCaption, describeMetricChange } from '../utils/report-period-comparison'
import { kpiGridColumnsClass } from '../utils/kpi-grid-columns'
import type {
  ReportCompareMode,
  ReportMeta,
  ReportMetricMeta,
  ReportMetricValues,
  ReportTrendPoint,
} from '../types/report-analytics'
import { KpiTrendCard } from './kpi-trend-card'

/** Chỉ số `snapshot` (vd công nợ) — số dư tại-một-thời-điểm, không cộng dồn theo kỳ. */
const SNAPSHOT_HINT = 'Số dư hiện tại — không có xu hướng theo kỳ'

interface ReportKpiRowProps {
  meta: ReportMeta
  /** `ReportPageConfig.kpis` — khóa chỉ số hiện thành thẻ, ĐÚNG THỨ TỰ. */
  kpis: string[]
  totals: { current: ReportMetricValues; compare: ReportMetricValues | null }
  trend: ReportTrendPoint[]
  compareMode: ReportCompareMode
  selectedMetric: string
  /** Bỏ trống = thẻ tĩnh, không bấm đổi biểu đồ (trang `hideTrend` không có biểu đồ để đổi). */
  onSelectMetric?: (metric: string) => void
  isLoading: boolean
  /** Chỉ số có danh sách (`meta.drilldown_metrics` ∩ `metrics`) — thẻ của chúng có nút «Xem danh sách». */
  drilldownMetrics?: ReadonlySet<string>
  onDrilldown?: (metric: string) => void
}

/**
 * Hàng thẻ KPI đầu trang báo cáo Haravan — bấm một thẻ để đổi chỉ số đang vẽ
 * trên biểu đồ xu hướng bên dưới (`ReportTrendChart`).
 *
 * Trước khi có lượt gọi API đầu tiên, `meta.metrics` rỗng nên chưa biết nhãn
 * thật của từng chỉ số — hiện khung xương THEO SỐ LƯỢNG `kpis` cấu hình thay
 * vì hiện tạm khóa kỹ thuật (vd "lines") làm nhãn.
 */
export function ReportKpiRow({
  meta,
  kpis,
  totals,
  trend,
  compareMode,
  selectedMetric,
  onSelectMetric,
  isLoading,
  drilldownMetrics,
  onDrilldown,
}: ReportKpiRowProps) {
  //  `helper` (mẫu số phụ của một derived) không bao giờ hiện thành thẻ, kể cả
  //  khi ai đó lỡ liệt kê nó trong `kpis` — backend là nguồn DUY NHẤT của cờ này.
  //  Khóa VẮNG MẶT khỏi `meta` (vd chỉ số tài khoản bị backend gỡ vì người xem thiếu
  //  `user.read`) cũng bị bỏ — hàng thẻ co lại, không vẽ thẻ trơ khóa kỹ thuật.
  const metrics = kpis
    .map((key) => meta.metrics.find((m) => m.key === key))
    .filter((m): m is ReportMetricMeta => m != null && !m.helper)

  if (metrics.length === 0) {
    if (!isLoading) return null
    return (
      <div className={cn('grid grid-cols-2 gap-3 sm:gap-4', kpiGridColumnsClass(kpis.length))}>
        {kpis.map((key) => (
          <Skeleton key={key} className="h-24 w-full" />
        ))}
      </div>
    )
  }

  return (
    <div className={cn('grid grid-cols-2 gap-3 sm:gap-4', kpiGridColumnsClass(metrics.length))}>
      {metrics.map((metric) => {
        //  `?? null`, KHÔNG `?? 0` — 0 là một giá trị THẬT, còn thiếu khóa/`null`
        //  nghĩa là "chưa có gì để đo" (chỉ số dẫn xuất mẫu số 0) và phải ra "—".
        const current = totals.current[metric.key] ?? null
        const compareValue = totals.compare?.[metric.key] ?? null
        const changeDescription =
          compareMode === 'none'
            ? undefined
            : describeMetricChange(current, compareValue, metric.kind, metric.good)
        //  `snapshot`: số dư tại-một-thời-điểm, KHÔNG có mặt trong `trend[]` —
        //  không vẽ sparkline (mọi mốc đều thiếu khóa) và không cho bấm đổi
        //  biểu đồ xu hướng (không có gì để vẽ).
        const sparkline = metric.snapshot
          ? undefined
          : trend.map((point) => point.current[metric.key] ?? 0)

        return (
          <KpiTrendCard
            key={metric.key}
            label={metric.label}
            value={formatReportMetricValue(current, metric.kind, 'compact')}
            changeDescription={changeDescription}
            changeCaption={compareMode === 'none' ? undefined : compareCaption(compareMode)}
            hint={
              metric.snapshot ? SNAPSHOT_HINT : compareMode === 'none' ? 'Không so sánh' : undefined
            }
            sparkline={sparkline}
            loading={isLoading}
            selected={!!onSelectMetric && metric.key === selectedMetric}
            onClick={
              metric.snapshot || !onSelectMetric ? undefined : () => onSelectMetric(metric.key)
            }
            action={
              onDrilldown && drilldownMetrics?.has(metric.key) ? (
                <Button
                  type="button"
                  variant="link"
                  size="sm"
                  className="h-auto gap-1 px-0 text-xs"
                  aria-label={`Xem danh sách ${metric.label}`}
                  onClick={() => onDrilldown(metric.key)}
                >
                  <List className="size-3.5" aria-hidden />
                  Xem danh sách
                </Button>
              ) : undefined
            }
          />
        )
      })}
    </div>
  )
}
