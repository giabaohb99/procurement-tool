import { extractErrorMessage } from '@/core/api'
import { HorizontalBarChart } from '@/shared/ui/horizontal-bar-chart'
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@/shared/ui/sheet'
import { Skeleton } from '@/shared/ui/skeleton'

import { useFeatureBreakdown } from '../../hooks/use-feature-usage'
import type { FeatureUsageParams } from '../../api/feature-usage-api'
import { screenName } from '../../utils/feature-usage-format'

interface Props {
  /** Chức năng đang xem; null = đóng. */
  target: { kind: number; code: number; route: string; title: string } | null
  /** Bộ lọc kỳ / pháp nhân / phòng ban đang áp ở trang. */
  filterParams: FeatureUsageParams
  onClose: () => void
}

/** Một chức năng theo phòng ban (và theo màn). KHÔNG có tên người — báo cáo chỉ gom theo phòng ban. */
export function FeatureUsageBreakdownSheet({ target, filterParams, onClose }: Props) {
  const { data, isLoading, isError, error } = useFeatureBreakdown(
    target ? { ...filterParams, kind: target.kind, code: target.code, route: target.route } : null,
  )
  const byDept = (data?.by_department ?? []).map((d) => ({ label: d.department_name || 'Chưa rõ phòng ban', value: d.uses }))
  const byRoute = (data?.by_route ?? []).filter((r) => r.route).map((r) => ({ label: screenName(r.route), value: r.uses }))

  return (
    <Sheet open={target !== null} onOpenChange={(open) => !open && onClose()}>
      <SheetContent className="w-full overflow-y-auto sm:max-w-lg">
        <SheetHeader>
          <SheetTitle>{target?.title}</SheetTitle>
          <SheetDescription>Số lần dùng theo phòng ban trong kỳ đang chọn.</SheetDescription>
        </SheetHeader>
        <div className="space-y-4 px-4 pb-4">
          {isLoading && <Skeleton className="h-40 w-full" />}
          {isError && <p className="text-sm text-destructive">{extractErrorMessage(error)}</p>}
          {data && byDept.length === 0 && <p className="text-sm text-muted-foreground">Chưa có ai dùng trong kỳ này.</p>}
          {byDept.length > 0 && (
            <div>
              <p className="mb-1 text-sm font-medium">Theo phòng ban</p>
              <HorizontalBarChart data={byDept} unit="lần" />
            </div>
          )}
          {byRoute.length > 1 && (
            <div>
              <p className="mb-1 text-sm font-medium">Theo màn hình</p>
              <HorizontalBarChart data={byRoute} unit="lần" />
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  )
}
