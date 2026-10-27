import { useMemo } from 'react'

import { extractErrorMessage } from '@/core/api'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@/shared/ui/sheet'
import { Skeleton } from '@/shared/ui/skeleton'

import { useReportDrilldown } from '../hooks/use-report-drilldown'
import type { ReportDrilldownTarget } from '../types/report-drilldown'
import { buildDrilldownParams } from '../utils/build-drilldown-params'
import { formatReportMetricValue } from '../utils/format-report-metric'
import type { ReportDrilldownMetricOption } from '../utils/report-drilldown-metrics'
import { ReportDrilldownTable } from './report-drilldown-table'

interface ReportDrilldownSheetProps {
  /** `ReportPageConfig.drilldownEndpoint` — `<gốc>/summary/rows`. */
  endpoint: string
  /** Tham số `/summary` đang xem (`useReportFilters().queryParams`). */
  baseParams: Record<string, string>
  /** Chỉ số + nhóm đang mở; `null` = ngăn đóng (và KHÔNG gọi API). */
  target: ReportDrilldownTarget | null
  /** Chỉ số có danh sách (`listDrilldownMetrics`) — ô chọn trong ngăn chỉ có các khóa này. */
  metricOptions: ReportDrilldownMetricOption[]
  onMetricChange: (metric: string) => void
  onClose: () => void
  /** `report.<slug>` — bảng nhớ bố cục theo `<storageKey>.rows.<metric>`. */
  storageKey: string
}

const formatCount = (n: number) => formatReportMetricValue(n, 'int')

/**
 * Ngăn «Danh sách người» (duoc-CR-686): bấm «Xem danh sách» ở thẻ KPI hay ở một dòng
 * «Xem theo» → ra đúng những người/đơn/hợp đồng làm nên con số đó, cùng bộ lọc trang.
 * Đổi chỉ số ngay trong ngăn, nhóm giữ nguyên.
 */
export function ReportDrilldownSheet({
  endpoint,
  baseParams,
  target,
  metricOptions,
  onMetricChange,
  onClose,
  storageKey,
}: ReportDrilldownSheetProps) {
  const params = useMemo(
    () => (target ? buildDrilldownParams(baseParams, target) : null),
    [baseParams, target],
  )
  const { data, isLoading, isError, error, refetch } = useReportDrilldown(endpoint, params)

  const scopeText = target?.group
    ? `${target.group.dimensionLabel}: ${target.group.label}`
    : 'Toàn bộ báo cáo'

  return (
    <Sheet open={target !== null} onOpenChange={(open) => !open && onClose()}>
      <SheetContent className="w-full gap-0 sm:max-w-3xl xl:max-w-5xl">
        <SheetHeader className="pr-10">
          <SheetTitle>Danh sách</SheetTitle>
          <SheetDescription>{scopeText} · cùng bộ lọc đang xem trên trang.</SheetDescription>
        </SheetHeader>

        <div className="flex min-h-0 flex-1 flex-col gap-3 px-4 pb-4">
          <div className="flex flex-wrap items-center gap-2">
            <Select value={target?.metric ?? ''} onValueChange={onMetricChange}>
              <SelectTrigger className="w-auto min-w-56 max-md:flex-1" aria-label="Chỉ số">
                <SelectValue placeholder="Chọn chỉ số" />
              </SelectTrigger>
              <SelectContent>
                {metricOptions.map((o) => (
                  <SelectItem key={o.key} value={o.key}>
                    {o.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {data && (
              <span className="text-sm text-muted-foreground">{formatCount(data.total)} dòng</span>
            )}
          </div>

          {data?.truncated && (
            <p className="rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-sm" role="status">
              Chỉ hiện {formatCount(data.rows.length)} dòng đầu trên tổng {formatCount(data.total)}. Thu
              hẹp bộ lọc (phòng ban, công ty, kỳ) để xem đủ.
            </p>
          )}

          {isError ? (
            <div className="space-y-2" role="alert">
              <p className="text-sm text-destructive">
                {extractErrorMessage(error) || 'Không tải được danh sách.'}
              </p>
              <Button type="button" variant="outline" size="sm" onClick={() => void refetch()}>
                Thử lại
              </Button>
            </div>
          ) : isLoading || !data ? (
            <div className="space-y-2" aria-label="Đang tải danh sách">
              <Skeleton className="h-9 w-full" />
              <Skeleton className="h-9 w-full" />
              <Skeleton className="h-9 w-full" />
            </div>
          ) : (
            <Card className="flex min-h-0 flex-1 flex-col p-3">
              <ReportDrilldownTable data={data} storageKey={`${storageKey}.rows.${data.metric.key}`} />
            </Card>
          )}
        </div>
      </SheetContent>
    </Sheet>
  )
}
