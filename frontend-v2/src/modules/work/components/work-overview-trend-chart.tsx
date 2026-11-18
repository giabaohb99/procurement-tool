import { CHART_COLORS, CHART_NEUTRAL } from '@/shared/ui/chart'
import { Skeleton } from '@/shared/ui/skeleton'
import { StackedColumnLineChart, type ComboSeries } from '@/shared/ui/stacked-column-line-chart'

import { useWorkOverviewTrend, type WorkOverviewTrendKind } from '../hooks/use-work-overview'

/**
 * Màu theo nghĩa, cùng họ với các biểu đồ khác của màn: "xong" họ xanh ngọc, trễ đỏ, không hạn xám, việc mới giao xanh
 * dương. Đã chạy bộ kiểm màu dataviz (nền sáng + tối): xanh ngọc / đỏ / xanh dương đạt mọi mục; xám tương phản thấp nên
 * có chú giải + tooltip ghi số bù lại.
 */
const DONE_BARS: ComboSeries[] = [
  { key: 'onTime', label: 'Xong đúng hạn', color: CHART_COLORS[2] },
  { key: 'late', label: 'Xong trễ hạn', color: 'var(--destructive)' },
  { key: 'noDue', label: 'Xong, không đặt hạn', color: CHART_NEUTRAL },
]
const CREATED_LINE: ComboSeries = { key: 'created', label: 'Việc mới giao', color: CHART_COLORS[0] }

interface WorkOverviewTrendChartProps {
  kind: WorkOverviewTrendKind
  /** `null` = chưa chọn đối tượng — không gọi API. */
  id: number | null
  periodDays: number
}

/**
 * Biểu đồ DIỄN BIẾN của một dự án / một người (duoc-CR-782): cột là việc xong mỗi ngày / tuần (đúng hạn / trễ / không
 * đặt hạn), đường là việc mới giao. Dùng ở khối "Theo dõi một dự án / một người" của màn Tổng quan và ở tab Báo cáo
 * trong chi tiết dự án.
 */
export function WorkOverviewTrendChart({ kind, id, periodDays }: WorkOverviewTrendChartProps) {
  const trend = useWorkOverviewTrend(kind, id, periodDays)
  const buckets = trend.data?.buckets ?? []
  const idle = buckets.every((b) => !b.created && !b.done_on_time && !b.done_late && !b.done_no_due)

  if (trend.isLoading) return <Skeleton className="h-72 w-full" />
  if (trend.isError) {
    return <p className="py-8 text-center text-sm text-destructive">Không tải được diễn biến. Thử tải lại trang.</p>
  }
  if (idle) {
    //  Cả kỳ không có gì: một biểu đồ phẳng lì ở 0 nhìn như lỗi tải — nói thẳng ra.
    return (
      <p className="rounded-lg border border-dashed py-10 text-center text-sm text-muted-foreground">
        Không có việc mới giao hay việc xong nào trong {periodDays} ngày qua.
      </p>
    )
  }
  return (
    <StackedColumnLineChart
      data={buckets.map((b) => ({
        label: b.label,
        values: { onTime: b.done_on_time, late: b.done_late, noDue: b.done_no_due, created: b.created },
      }))}
      bars={DONE_BARS}
      line={CREATED_LINE}
      unit="việc xong"
    />
  )
}
