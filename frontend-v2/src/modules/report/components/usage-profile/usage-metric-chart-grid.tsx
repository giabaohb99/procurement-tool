import { Card } from '@/shared/ui/card'
import { Skeleton } from '@/shared/ui/skeleton'

import type { UsageMetricCatalogItem } from '../../types/usage-metric-catalog'
import { UsageMetricChartCard } from './usage-metric-chart-card'

interface Props {
  items: UsageMetricCatalogItem[] | undefined
  hasWeek: boolean
  isLoading: boolean
  isError: boolean
  errorMessage?: string
}

/** Lưới thẻ biểu đồ: 1 cột trên điện thoại, 2 cột từ md, 3 cột từ xl. */
export function UsageMetricChartGrid({ items, hasWeek, isLoading, isError, errorMessage }: Props) {
  if (isError) return <Card className="p-4 text-sm text-destructive">{errorMessage ?? 'Không tải được dữ liệu.'}</Card>
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {[0, 1, 2].map((i) => <Skeleton key={i} className="h-72 w-full" />)}
      </div>
    )
  }
  if (!items?.length) return <Card className="p-4 text-sm text-muted-foreground">Chưa có chỉ số nào trong nhóm này.</Card>
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
      {items.map((m) => <UsageMetricChartCard key={m.key} item={m} hasWeek={hasWeek} />)}
    </div>
  )
}
