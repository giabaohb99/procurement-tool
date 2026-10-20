import { Badge } from '@/shared/ui/badge'

import { unmeasuredReasonLabel } from '../../config/usage-metric-labels'
import type { UsageMetricCatalogItem } from '../../types/usage-metric-catalog'
import { formatUsageValue } from '../../utils/usage-format'
import { unitKind, unmeasuredStatusText } from '../../utils/usage-metric-catalog-helpers'

/** Trạng thái đo THỰC của tuần snapshot mới nhất: «n/tổng người · trung vị …» hoặc lý do chưa đo. */
export function UsageMetricStatusCell({ item, hasWeek }: { item: UsageMetricCatalogItem; hasWeek: boolean }) {
  if (!hasWeek) return <Badge variant="outline">{unmeasuredStatusText(false, null)}</Badge>
  if (item.measured_users > 0) {
    return (
      <div className="space-y-0.5">
        <div className="tabular-nums">
          {item.measured_users}/{item.total_users} người đã đo
        </div>
        <div className="text-xs text-muted-foreground tabular-nums">
          Trung vị công ty: {formatUsageValue(item.company_median, unitKind(item.unit))}
        </div>
      </div>
    )
  }
  const reason = item.unmeasured_reason
  const text = unmeasuredStatusText(true, reason)
  return (
    <Badge variant="outline" title={reason ? `Lý do: ${unmeasuredReasonLabel(reason)}` : undefined}>
      {text ?? 'Chưa đo được'}
    </Badge>
  )
}
