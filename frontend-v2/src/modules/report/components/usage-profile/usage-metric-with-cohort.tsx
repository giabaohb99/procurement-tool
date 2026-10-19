import { ArrowDown, ArrowUp, Minus } from 'lucide-react'

import { cn } from '@/shared/utils/cn'

import { USAGE_METRIC_LABELS, metricLabel, unmeasuredReasonLabel } from '../../config/usage-metric-labels'
import type { UsageSnapshot } from '../../types/usage-profile'
import { formatUsageValue } from '../../utils/usage-format'

/** Mũi tên xu hướng so giá trị đầu và cuối của 4 tuần; thiếu số hoặc đi ngang → gạch ngang. */
function Trend({ trend }: { trend?: (number | null)[] }) {
  const points = (trend ?? []).filter((v): v is number => v != null)
  if (points.length < 2) return null
  const delta = points[points.length - 1] - points[0]
  const Icon = delta > 0 ? ArrowUp : delta < 0 ? ArrowDown : Minus
  const text = delta > 0 ? 'tăng' : delta < 0 ? 'giảm' : 'đi ngang'
  return (
    <span className="inline-flex items-center text-muted-foreground" title={`Xu hướng ${points.length} tuần: ${text}`}>
      <Icon className="size-3.5" aria-label={`Xu hướng ${text}`} />
    </span>
  )
}

interface UsageMetricWithCohortProps {
  snapshot: UsageSnapshot
  metricKey: string
  className?: string
}

/**
 * Một chỉ số: giá trị + «nhóm: trung vị» + xu hướng. Chỉ số CHƯA ĐO ĐƯỢC (có mặt trong
 * `unmeasured` hoặc không có giá trị) hiện «Chưa đo được — {lý do}», KHÔNG BAO GIỜ hiện 0.
 */
export function UsageMetricWithCohort({ snapshot, metricKey, className }: UsageMetricWithCohortProps) {
  const metric = snapshot.metrics[metricKey]
  const reasonCode = snapshot.unmeasured?.[metricKey]
  const kind = USAGE_METRIC_LABELS[metricKey]?.kind ?? 'count'
  const measured = metric?.v != null && reasonCode === undefined

  return (
    <div className={cn('rounded-md border p-3', className)}>
      <p className="text-xs text-muted-foreground">{metricLabel(metricKey)}</p>
      {measured ? (
        <div className="mt-1 flex items-baseline gap-2">
          <span className="text-lg font-semibold tabular-nums">{formatUsageValue(metric.v, kind)}</span>
          <Trend trend={metric.trend} />
          {metric.med != null && (
            <span className="text-xs text-muted-foreground">nhóm: {formatUsageValue(metric.med, kind)}</span>
          )}
        </div>
      ) : (
        <p className="mt-1 text-sm text-muted-foreground">
          Chưa đo được{reasonCode !== undefined && ` — ${unmeasuredReasonLabel(reasonCode)}`}
        </p>
      )}
    </div>
  )
}
