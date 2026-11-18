import { Badge } from '@/shared/ui/badge'
import { Card, CardContent } from '@/shared/ui/card'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'

import type { WorkOverview, WorkOverviewProject } from '../hooks/use-work-overview'
import { PROJECT_HEALTH_TONE } from '../utils/project-health-tone'

const num = (value: number | undefined) => (value ?? 0).toLocaleString('vi-VN')

interface WorkProjectReportSummaryProps {
  data: WorkOverview | undefined
  project: WorkOverviewProject | undefined
  periodDays: number
  isLoading: boolean
}

/** Một dòng số của thẻ tóm tắt: nhãn bên trái, số bên phải, chú thích nhỏ dưới nhãn. */
function SummaryRow({
  label,
  value,
  hint,
  tone,
}: {
  label: string
  value: string
  hint?: string
  tone?: 'danger' | 'warning'
}) {
  return (
    <div className="flex items-baseline justify-between gap-3 py-2">
      <div className="min-w-0">
        <p className="text-sm text-muted-foreground">{label}</p>
        {hint && <p className="text-xs text-muted-foreground/80">{hint}</p>}
      </div>
      <p
        className={cn(
          'shrink-0 text-base font-semibold tabular-nums',
          tone === 'danger' && 'text-destructive',
          tone === 'warning' && 'text-warning',
        )}
      >
        {value}
      </p>
    </div>
  )
}

/**
 * Thẻ TÓM TẮT đứng đầu cột phải của báo cáo từng dự án (duoc-CR-782, bố cục "cột phải cố định" anh Được chọn).
 *
 * Thay sáu ô số to của bản trước: trong chi tiết dự án, cây dự án bên trái đã ăn mất một khúc bề ngang nên sáu ô bị bóp,
 * chữ gợi ý gãy hai dòng. Ở đây % hoàn thành là con số lớn duy nhất, các số còn lại xếp dọc nhãn-trái số-phải.
 */
export function WorkProjectReportSummary({ data, project, periodDays, isLoading }: WorkProjectReportSummaryProps) {
  if (isLoading) {
    return (
      <Card className="py-4">
        <CardContent className="space-y-3 px-4">
          <Skeleton className="h-10 w-24" />
          <Skeleton className="h-2 w-full" />
          {[0, 1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-6 w-full" />
          ))}
        </CardContent>
      </Card>
    )
  }

  const progress = project?.progress ?? 0
  const overdue = data?.task_overdue ?? 0
  const overdueShare = data?.task_open ? Math.round((overdue * 100) / data.task_open) : 0
  const onTime = data?.on_time_rate ?? null

  return (
    <Card className="gap-0 py-4">
      <CardContent className="px-4">
        <div className="flex items-start justify-between gap-2">
          <div>
            <p className="text-3xl font-semibold tabular-nums">{progress}%</p>
            <p className="text-sm text-muted-foreground">hoàn thành</p>
          </div>
          {project && (
            <Badge variant="outline" className={cn('mt-1 font-medium', PROJECT_HEALTH_TONE[project.health])}>
              {project.health_label}
            </Badge>
          )}
        </div>
        <span
          className="mt-3 block h-2 overflow-hidden rounded-full bg-muted"
          role="progressbar"
          aria-label="Tiến độ hoàn thành"
          aria-valuenow={progress}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <span className="block h-full rounded-full bg-primary" style={{ width: `${progress}%` }} />
        </span>
        <p className="mt-1.5 text-xs text-muted-foreground tabular-nums">
          {num(project?.done)}/{num(project?.total)} việc đã xong (không tính việc hủy)
        </p>

        <div className="mt-3 divide-y border-t">
          <SummaryRow
            label="Việc đang mở"
            value={num(data?.task_open)}
            hint={`${num(data?.task_created_in_period)} việc mới trong ${periodDays} ngày`}
          />
          <SummaryRow
            label="Quá hạn"
            value={num(overdue)}
            //  Tô đỏ một số 0 là báo động giả.
            hint={overdue ? `${overdueShare}% số việc đang mở` : undefined}
            tone={overdue ? 'danger' : undefined}
          />
          <SummaryRow label={`Xong trong ${periodDays} ngày`} value={num(data?.task_done_in_period)} />
          <SummaryRow
            label="Xong đúng hạn"
            //  `null` = chưa có việc xong nào có hạn để đo — hiện gạch, không hiện 0%.
            value={onTime === null ? '—' : `${onTime}%`}
            hint="Trên số việc xong trong kỳ có đặt hạn"
            tone={onTime !== null && onTime < 50 ? 'warning' : undefined}
          />
          <SummaryRow
            label="Chưa ai nhận"
            value={num(data?.task_unassigned)}
            tone={data?.task_unassigned ? 'warning' : undefined}
          />
          <SummaryRow label="Chưa đặt hạn" value={num(data?.task_no_due)} />
          <SummaryRow label="Hạn chót dự án" value={project?.last_due ? formatDate(project.last_due) : '—'} />
        </div>
      </CardContent>
    </Card>
  )
}
