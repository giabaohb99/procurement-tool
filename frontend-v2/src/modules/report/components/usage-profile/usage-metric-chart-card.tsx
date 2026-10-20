import { Info } from 'lucide-react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Badge } from '@/shared/ui/badge'
import { Card } from '@/shared/ui/card'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'

import { USAGE_METRIC_DEFINITIONS } from '../../config/usage-metric-definitions'
import { metricLabel } from '../../config/usage-metric-labels'
import type { UsageMetricCatalogItem } from '../../types/usage-metric-catalog'
import { formatUsageValue } from '../../utils/usage-format'
import { goodWhenLabel, unitKind, unmeasuredStatusText } from '../../utils/usage-metric-catalog-helpers'
import { UsageMetricHistogram } from './usage-metric-histogram'
import { UsageMetricTrend } from './usage-metric-trend'

interface Props {
  item: UsageMetricCatalogItem
  /** Đã có bản chụp tuần nào chưa. */
  hasWeek: boolean
}

/** Nút ⓘ mở ý nghĩa / cách tính / nguồn dữ liệu của chỉ số. */
function DefinitionPopover({ metricKey }: { metricKey: string }) {
  const def = USAGE_METRIC_DEFINITIONS[metricKey]
  if (!def) return null
  const rows: [string, string][] = [['Ý nghĩa', def.meaning], ['Cách tính', def.formula], ['Nguồn dữ liệu', def.source]]
  return (
    <Popover>
      <PopoverTrigger asChild>
        <button type="button" aria-label={`Xem định nghĩa: ${metricLabel(metricKey)}`} className="text-muted-foreground hover:text-foreground">
          <Info className="size-4" />
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-80 space-y-2 text-sm">
        {rows.map(([title, text]) => (
          <div key={title}>
            <div className="font-semibold">{title}</div>
            <div className="text-muted-foreground">{text}</div>
          </div>
        ))}
      </PopoverContent>
    </Popover>
  )
}

/** Thẻ biểu đồ của một chỉ số: phân phối tuần mới nhất + xu hướng trung vị theo tuần (duoc-CR-651). */
export function UsageMetricChartCard({ item, hasWeek }: Props) {
  const measured = item.measured_users > 0
  const kind = unitKind(item.unit)
  return (
    <Card className="h-full min-w-0 gap-3 p-4">
      <div className="space-y-1">
        <div className="flex items-center justify-between gap-2">
          <h3 className="min-w-0 truncate text-base font-semibold" title={metricLabel(item.key)}>{metricLabel(item.key)}</h3>
          <DefinitionPopover metricKey={item.key} />
        </div>
        {measured ? (
          <p className="text-xs text-muted-foreground tabular-nums">
            {item.measured_users}/{item.total_users} người · trung vị {formatUsageValue(item.company_median, kind)} · tốt khi{' '}
            {goodWhenLabel(item.direction).toLowerCase()}
          </p>
        ) : (
          <p className="text-xs text-muted-foreground">Tốt khi {goodWhenLabel(item.direction).toLowerCase()}</p>
        )}
      </div>
      {measured ? (
        <>
          <div>
            <div className="text-xs font-medium text-muted-foreground">Số người theo giá trị</div>
            <UsageMetricHistogram
              buckets={item.histogram}
              unit={item.unit}
              median={item.company_median}
              medianText={`Trung vị ${formatUsageValue(item.company_median, kind)}`}
            />
          </div>
          <div>
            <div className="text-xs font-medium text-muted-foreground">Trung vị công ty theo tuần</div>
            {item.trend.length <= 1 && <p className="text-xs text-muted-foreground">Mới có 1 tuần số liệu</p>}
            <UsageMetricTrend points={item.trend} unit={item.unit} />
          </div>
          <Link className="mt-auto self-start text-sm text-primary underline-offset-2 hover:underline" to={appRoutes.report.usageProfilesByMetric(item.key)}>
            Xem xếp hạng →
          </Link>
        </>
      ) : (
        <div className="flex flex-1 items-center justify-center py-8">
          <Badge variant="outline">{unmeasuredStatusText(hasWeek, item.unmeasured_reason) ?? 'Chưa đo được'}</Badge>
        </div>
      )}
    </Card>
  )
}
