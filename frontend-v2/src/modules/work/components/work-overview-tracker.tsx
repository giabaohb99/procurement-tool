import { LineChart as LineChartIcon } from 'lucide-react'
import { useState } from 'react'

import { Badge } from '@/shared/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import { SearchSelect, type SearchSelectOption } from '@/shared/ui/search-select'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'

import type { WorkOverview, WorkOverviewTrendKind } from '../hooks/use-work-overview'
import { PROJECT_HEALTH_TONE } from '../utils/project-health-tone'
import { trendStepLabel } from '../utils/trend-step-label'
import { WorkOverviewTrendChart } from './work-overview-trend-chart'

/** Một ô số nhỏ của đối tượng đang chọn. */
function Fact({ label, value, tone }: { label: string; value: string; tone?: 'danger' | 'muted' }) {
  return (
    <div className="rounded-lg border bg-muted/30 px-3 py-2">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p
        className={cn(
          'text-lg font-semibold tabular-nums',
          tone === 'danger' && 'text-destructive',
          tone === 'muted' && 'text-muted-foreground',
        )}
      >
        {value}
      </p>
    </div>
  )
}

interface WorkOverviewTrackerProps {
  /** Tab Dự án theo dõi một dự án, tab Nhân sự theo dõi một người. */
  kind: WorkOverviewTrendKind
  data: WorkOverview | undefined
  periodDays: number
}

/**
 * THEO DÕI MỘT DỰ ÁN / MỘT NGƯỜI (duoc-CR-782) — anh Được hỏi biểu đồ có theo dõi được từng dự án, hiệu suất từng
 * người không. Đứng ở tab Dự án (`kind="project"`) và tab Nhân sự (`kind="person"`). Chọn một đối tượng → dải số của riêng nó + diễn biến theo ngày (kỳ ≤ 31 ngày) hoặc tuần: cột là việc
 * XONG (đúng hạn / trễ / không hạn), đường là việc MỚI GIAO. Đường nằm trên cột nhiều mốc liền là việc đang dồn lên.
 *
 * Danh sách chọn lấy từ chính số liệu màn (dự án / người trong phạm vi xem), mặc định đối tượng đáng lo nhất — máy chủ
 * đã xếp dự án trễ và người nhiều việc quá hạn lên đầu.
 */
export function WorkOverviewTracker({ kind, data, periodDays }: WorkOverviewTrackerProps) {
  const [chosen, setChosen] = useState<number | null>(null)

  const projects = data?.projects ?? []
  const people = data?.people ?? []
  const options: SearchSelectOption[] =
    kind === 'project'
      ? projects.map((p) => ({ value: String(p.list_id), label: p.name, hint: p.health_label }))
      : people.map((p) => ({
          value: String(p.employee_id),
          label: p.name || `Nhân sự #${p.employee_id}`,
          hint: p.code,
          avatar: p.avatar,
        }))
  //  Chưa chọn (hoặc đối tượng đã chọn không còn trong phạm vi) thì lấy dòng đầu.
  const fallback = options[0] ? Number(options[0].value) : null
  const selectedId = chosen !== null && options.some((o) => Number(o.value) === chosen) ? chosen : fallback

  const project = kind === 'project' ? projects.find((p) => p.list_id === selectedId) : undefined
  const person = kind === 'person' ? people.find((p) => p.employee_id === selectedId) : undefined
  const step = trendStepLabel(periodDays)

  return (
    <Card className="gap-3">
      <CardHeader className="max-md:px-4">
        <CardTitle className="flex items-center gap-2 text-base">
          <LineChartIcon className="size-4 text-muted-foreground" />
          {kind === 'project' ? 'Theo dõi một dự án' : 'Theo dõi một người'}
        </CardTitle>
        <CardDescription>
          Chọn {kind === 'project' ? 'một dự án' : 'một người'} để xem diễn biến trong {periodDays} ngày, theo từng {step}: cột là việc xong
          (đúng hạn / trễ / không đặt hạn), đường là việc mới giao. Đường nằm trên cột nhiều {step} liền là việc đang dồn
          lên.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4 max-md:px-4">
        <div className="flex flex-wrap items-center gap-2">
          <div className="w-full sm:w-80">
            <SearchSelect
              value={selectedId === null ? '' : String(selectedId)}
              onChange={(value) => setChosen(Number(value))}
              options={options}
              placeholder={kind === 'project' ? 'Chọn dự án…' : 'Chọn người…'}
              searchPlaceholder={kind === 'project' ? 'Tìm dự án…' : 'Tìm người…'}
              emptyMessage="Không có trong phạm vi đang xem."
            />
          </div>
          {project && (
            <Badge variant="outline" className={cn('font-medium', PROJECT_HEALTH_TONE[project.health])}>
              {project.health_label}
            </Badge>
          )}
        </div>

        {options.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">
            {kind === 'project' ? 'Chưa có dự án nào trong phạm vi đang xem.' : 'Chưa có việc nào được giao cho ai.'}
          </p>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
              {project && (
                <>
                  <Fact label="Đang mở" value={project.open.toLocaleString('vi-VN')} />
                  <Fact label="Quá hạn" value={project.overdue.toLocaleString('vi-VN')} tone={project.overdue ? 'danger' : 'muted'} />
                  <Fact label={`Xong trong ${periodDays} ngày`} value={project.done_in_period.toLocaleString('vi-VN')} />
                  <Fact label="Hoàn thành" value={`${project.progress}%`} />
                  <Fact label="Hạn chót" value={project.last_due ? formatDate(project.last_due) : '—'} tone={project.last_due ? undefined : 'muted'} />
                </>
              )}
              {person && (
                <>
                  <Fact label="Đang mở" value={person.open.toLocaleString('vi-VN')} />
                  <Fact label="Quá hạn" value={person.overdue.toLocaleString('vi-VN')} tone={person.overdue ? 'danger' : 'muted'} />
                  <Fact label={`Xong trong ${periodDays} ngày`} value={person.done_in_period.toLocaleString('vi-VN')} />
                  <Fact
                    label="Xong đúng hạn"
                    value={person.on_time_rate === null ? '—' : `${person.on_time_rate}%`}
                    tone={person.on_time_rate === null ? 'muted' : person.on_time_rate < 50 ? 'danger' : undefined}
                  />
                  <Fact
                    label="Trễ lâu nhất"
                    value={person.max_overdue_days ? `${person.max_overdue_days} ngày` : '—'}
                    tone={person.max_overdue_days ? 'danger' : 'muted'}
                  />
                </>
              )}
            </div>

            <WorkOverviewTrendChart kind={kind} id={selectedId} periodDays={periodDays} />
          </>
        )}
      </CardContent>
    </Card>
  )
}
