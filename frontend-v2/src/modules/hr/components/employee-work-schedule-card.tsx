import { CalendarClock } from 'lucide-react'
import { Link } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { SectionHeading } from '@/shared/ui/section-heading'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatDate } from '@/shared/utils/format-date'
import { useEffectiveWorkSchedule } from '../hooks/use-effective-work-schedule'
import {
  SYSTEM_LEVEL_LABEL,
  WORK_SCHEDULE_LEVEL_CODE,
  type EffectiveWorkSchedule,
  type WorkScheduleDay,
} from '../types/work-schedule'
import {
  WEEKDAY_LABELS,
  fillWeek,
  formatWorkdays,
  presentWeekdays,
  sumWeeklyWorkdays,
} from '../utils/work-schedule-week'
import { describeDay, describeLunch } from '../utils/work-schedule-week-summary'

interface EmployeeWorkScheduleCardProps {
  employeeId: number
}

/** Nguồn của lịch: «Gán riêng» / «Theo phòng ban: …» / «Theo pháp nhân: …» / «Toàn hệ thống» / «Mặc định hệ thống». */
function describeSource(schedule: EffectiveWorkSchedule): string {
  if (schedule.is_fallback) return 'Mặc định hệ thống'
  const target = schedule.target_name ? `: ${schedule.target_name}` : ''
  switch (schedule.level) {
    case WORK_SCHEDULE_LEVEL_CODE.EMPLOYEE:
      return 'Gán riêng'
    case WORK_SCHEDULE_LEVEL_CODE.DEPARTMENT:
      return `Theo phòng ban${target}`
    case WORK_SCHEDULE_LEVEL_CODE.COMPANY:
      return `Theo pháp nhân${target}`
    case WORK_SCHEDULE_LEVEL_CODE.SYSTEM:
      return SYSTEM_LEVEL_LABEL
    default:
      return schedule.level_label ?? 'Không rõ nguồn'
  }
}

/** «Từ 01/11/2026 · Không thời hạn» hoặc «Từ … đến …»; không có ngày bắt đầu thì để trống. */
function describeValidity(schedule: EffectiveWorkSchedule): string {
  if (schedule.is_fallback || !schedule.effective_from) return ''
  const to = schedule.effective_to ? `đến ${formatDate(schedule.effective_to)}` : 'Không thời hạn'
  return `Từ ${formatDate(schedule.effective_from)} · ${to}`
}

/** Thứ nào backend không trả thì không có trong Map -> chip hiện «—», không bịa thành «Nghỉ». */
function indexByWeekday(days: unknown): Map<number, WorkScheduleDay> {
  const present = presentWeekdays(days)
  return new Map(fillWeek(days).filter((d) => present.has(d.weekday)).map((d) => [d.weekday, d]))
}

/**
 * Thẻ «Lịch làm việc» trên hồ sơ nhân sự: nhân sự này đang theo mẫu nào, lấy từ
 * cấp nào, và bảy ngày trong tuần ra sao. Là thẻ PHỤ — lỗi (404 ngoài phạm vi,
 * 403…) chỉ hiện một câu ngắn, không toast, không chặn phần còn lại của hồ sơ.
 *
 * Gác bằng chính quyền đọc hồ sơ (backend `employee.read` + phạm vi), KHÔNG đòi
 * `work_schedule.read`: prod không tự cấp khóa mới cho vai trò cũ.
 */
export function EmployeeWorkScheduleCard({ employeeId }: EmployeeWorkScheduleCardProps) {
  const { can } = usePermission()
  const { data, isLoading, isError } = useEffectiveWorkSchedule(employeeId)
  const canAssign = can('work_schedule', 'write')

  return (
    <Card className="gap-4 p-3 sm:p-5">
      <SectionHeading>Lịch làm việc</SectionHeading>

      {isLoading && (
        <div className="space-y-2" aria-busy="true">
          <Skeleton className="h-5 w-56" />
          <Skeleton className="h-12 w-full" />
        </div>
      )}

      {isError && (
        <p className="text-sm text-muted-foreground">
          Không xem được lịch làm việc của nhân sự này.
        </p>
      )}

      {data && <ScheduleBody schedule={data} canAssign={canAssign} />}
    </Card>
  )
}

function ScheduleBody({
  schedule,
  canAssign,
}: {
  schedule: EffectiveWorkSchedule
  canAssign: boolean
}) {
  const byWeekday = indexByWeekday(schedule.days)
  const hasDays = byWeekday.size > 0
  const total = hasDays ? sumWeeklyWorkdays(schedule.days) : (schedule.weekly_workdays ?? 0)
  const validity = describeValidity(schedule)

  return (
    <>
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <CalendarClock className="size-4 text-muted-foreground" />
        <span className="font-medium">{schedule.schedule_name}</span>
        <Badge variant="secondary">{describeSource(schedule)}</Badge>
        {validity && <span className="text-muted-foreground">{validity}</span>}
      </div>

      <ul className="grid grid-cols-4 gap-2 text-center text-sm sm:grid-cols-7">
        {WEEKDAY_LABELS.map((label, weekday) => {
          const day = byWeekday.get(weekday)
          return (
            <li key={label} className="rounded-md border px-1 py-2">
              <div className="text-xs font-semibold text-muted-foreground">{label}</div>
              <div className="font-medium">{day ? describeDay(day) : '—'}</div>
              {day && describeLunch(day) && (
                <div className="text-xs text-muted-foreground">{describeLunch(day)}</div>
              )}
            </li>
          )
        })}
      </ul>

      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm text-muted-foreground">{formatWorkdays(total)} ngày công/tuần</p>
        {canAssign && (
          <Button variant="outline" size="sm" asChild>
            <Link to={appRoutes.hr.workScheduleAssignments}>Gán lịch</Link>
          </Button>
        )}
      </div>
    </>
  )
}
