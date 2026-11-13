import { CalendarClock, CalendarPlus, ListChecks } from 'lucide-react'
import { Link } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { SectionHeading } from '@/shared/ui/section-heading'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatDate } from '@/shared/utils/format-date'
import { useDepartmentWorkSchedule } from '../hooks/use-department-work-schedule'
import {
  WORK_SCHEDULE_LEVEL_CODE,
  type EffectiveDepartmentWorkSchedule,
  type WorkScheduleAssignment,
} from '../types/work-schedule'
import { describeDepartmentScheduleSource } from '../utils/describe-department-schedule-source'
import {
  buildAssignmentCreateUrl,
  buildAssignmentListUrl,
} from '../utils/work-schedule-assignment-prefill'
import { formatWorkdays, resolveWeeklyWorkdays } from '../utils/work-schedule-week'
import { WorkScheduleWeekGrid } from './work-schedule-week-grid'

interface DepartmentWorkScheduleTabProps {
  departmentId: number
  /** Tên phòng — điền sẵn vào ô Đối tượng của hộp gán lịch lúc danh sách chưa tải xong. */
  departmentName: string
}

/**
 * Tab "Lịch làm việc" ở trang chi tiết phòng ban (duoc-CR-757): phòng đang theo mẫu lịch nào,
 * lấy từ cấp nào, bảy ngày ra sao, và các dòng gán lịch CẤP PHÒNG BAN của chính phòng này.
 *
 * Gác bằng chính quyền mở trang (`department.read` ở backend), KHÔNG đòi `work_schedule.read`
 * để xem; hai nút đi sang màn Gán lịch thì mới xét `work_schedule`. Lỗi (403 / 404) chỉ hiện
 * một câu, không toast, không chặn phần còn lại của trang.
 */
export function DepartmentWorkScheduleTab({ departmentId, departmentName }: DepartmentWorkScheduleTabProps) {
  const { can } = usePermission()
  const { data, isLoading, isError } = useDepartmentWorkSchedule(departmentId)
  const canCreate = can('work_schedule', 'create')
  const canBrowse = can('work_schedule', 'read')

  return (
    <Card className="gap-4 p-3 sm:p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        {/*  Khổ hẹp: tiêu đề chiếm trọn hàng, hai nút xuống hàng dưới — để chung một hàng thì
             tiêu đề bị bóp còn một chữ mỗi dòng. */}
        <SectionHeading className="min-w-0 flex-1 max-sm:basis-full">Lịch làm việc của phòng</SectionHeading>
        <div className="flex flex-wrap items-center gap-2">
          {canBrowse && (
            <Button variant="ghost" size="sm" asChild>
              <Link to={buildAssignmentListUrl(WORK_SCHEDULE_LEVEL_CODE.DEPARTMENT)}>
                <ListChecks />
                Xem gán lịch
              </Link>
            </Button>
          )}
          {canCreate && (
            <Button variant="outline" size="sm" asChild>
              <Link
                to={buildAssignmentCreateUrl({
                  level: WORK_SCHEDULE_LEVEL_CODE.DEPARTMENT,
                  targetId: departmentId,
                  targetName: data?.department_name || departmentName,
                })}
              >
                <CalendarPlus />
                Gán lịch cho phòng
              </Link>
            </Button>
          )}
        </div>
      </div>

      {isLoading && (
        <div className="space-y-2" aria-busy="true">
          <Skeleton className="h-5 w-72" />
          <Skeleton className="h-14 w-full" />
        </div>
      )}

      {isError && (
        <p className="text-sm text-muted-foreground">Không xem được lịch làm việc của phòng ban này.</p>
      )}

      {data && <ScheduleBody schedule={data} />}
    </Card>
  )
}

function ScheduleBody({ schedule }: { schedule: EffectiveDepartmentWorkSchedule }) {
  return (
    <>
      <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm">
        <CalendarClock className="size-4 text-muted-foreground" />
        <span className="font-medium">{schedule.schedule_name}</span>
        <span className="text-muted-foreground">{describeDepartmentScheduleSource(schedule)}</span>
      </div>

      <WorkScheduleWeekGrid days={schedule.days} />

      <div className="space-y-1 text-sm text-muted-foreground">
        <p>{formatWorkdays(resolveWeeklyWorkdays(schedule))} ngày công/tuần</p>
        <p>Nhân sự nào được gán lịch riêng thì theo lịch riêng đó, không theo lịch của phòng.</p>
      </div>

      <AssignmentList rows={Array.isArray(schedule.assignments) ? schedule.assignments : []} />
    </>
  )
}

/** Các dòng gán lịch cấp phòng ban của phòng này — backend đã xếp mới nhất trước. */
function AssignmentList({ rows }: { rows: WorkScheduleAssignment[] }) {
  return (
    <div className="space-y-2">
      <SectionHeading>Gán lịch riêng cho phòng</SectionHeading>
      {rows.length === 0 ? (
        <p className="text-sm text-muted-foreground">Phòng này chưa có dòng gán lịch riêng.</p>
      ) : (
        <ul className="divide-y rounded-md border text-sm">
          {rows.map((row) => (
            <li key={row.id} className="flex flex-wrap items-center gap-x-3 gap-y-1 px-3 py-2">
              <span className="min-w-0 flex-1 font-medium">{row.schedule_name}</span>
              <span className="text-muted-foreground">
                Từ {formatDate(row.effective_from) || '—'} ·{' '}
                {row.effective_to ? `đến ${formatDate(row.effective_to)}` : 'Không thời hạn'}
              </span>
              {row.is_current && <Badge>Đang áp</Badge>}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
