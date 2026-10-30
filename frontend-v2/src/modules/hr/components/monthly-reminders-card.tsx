import { Cake, ChevronLeft, ChevronRight, FileClock, PartyPopper, type LucideIcon } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'
import { useMonthlyReminders } from '../hooks/use-monthly-reminders'
import type { MonthlyReminderGroupKey } from '../types/monthly-reminders'
import {
  buildMonthlyReminderGroups,
  CONTRACT_LOOKAHEAD_DAYS,
  formatMonthKeyLabel,
  isPastContractLookahead,
  monthKeyToDate,
  shiftMonthKey,
  toMonthKey,
  type MonthlyReminderGroup,
  type MonthlyReminderRow,
} from '../utils/monthly-reminders'
import { LeaveCalendarMonthPicker } from './leave-calendar-month-picker'

const GROUP_ICONS: Record<MonthlyReminderGroupKey, LucideIcon> = {
  birthdays: Cake,
  anniversaries: PartyPopper,
  expiring_contracts: FileClock,
}

/** Số cột ở khổ rộng theo số nhóm ĐANG HIỆN — một nhóm thì không chừa hai cột trống. */
const GRID_COLS: Record<number, string> = { 1: 'md:grid-cols-1', 2: 'md:grid-cols-2', 3: 'md:grid-cols-3' }

interface MonthlyRemindersCardProps {
  className?: string
  /** "Hôm nay" do trang truyền xuống — tháng mở đầu tiên; bài kiểm truyền ngày cố định. */
  today?: Date
}

/**
 * Ô "Lịch nhắc trong tháng" (E3, duoc-CR-689): sinh nhật · kỷ niệm năm làm việc · HĐ / thử việc
 * hết hạn trong tháng đang chọn, mỗi dòng bấm mở hồ sơ. Nơi gọi chỉ dựng khi có `employee.read`.
 *
 * Nhóm nào người xem thiếu quyền thì backend bỏ khóa → nhóm đó KHÔNG hiện (kể cả khung). Không
 * còn nhóm nào thì nói thẳng là thiếu quyền, đừng để một ô trắng trông như đang tải hỏng.
 */
export function MonthlyRemindersCard({ className, today }: MonthlyRemindersCardProps) {
  const [now] = useState(() => today ?? new Date())
  const [month, setMonth] = useState(() => toMonthKey(now))
  const query = useMonthlyReminders(month, true)
  const groups = buildMonthlyReminderGroups(query.data)

  return (
    <Card className={cn('min-w-0 gap-4', className)}>
      <CardHeader className="flex flex-wrap items-start justify-between gap-2 pb-0">
        <div className="min-w-0">
          <CardTitle className="text-base text-navy dark:text-foreground">Lịch nhắc trong tháng</CardTitle>
          <CardDescription>Sinh nhật, kỷ niệm năm làm việc, hợp đồng và thử việc hết hạn.</CardDescription>
        </div>
        <div className="flex items-center gap-1">
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            aria-label="Tháng trước"
            onClick={() => setMonth((m) => shiftMonthKey(m, -1, now))}
          >
            <ChevronLeft className="size-4" />
          </Button>
          <LeaveCalendarMonthPicker
            anchor={monthKeyToDate(month, now)}
            label={formatMonthKeyLabel(month, now)}
            onJump={(d) => setMonth(toMonthKey(d))}
            className="ml-0"
          />
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            aria-label="Tháng sau"
            onClick={() => setMonth((m) => shiftMonthKey(m, 1, now))}
          >
            <ChevronRight className="size-4" />
          </Button>
        </div>
      </CardHeader>

      <CardContent>
        {query.isLoading ? (
          <div className="grid gap-4 md:grid-cols-3">
            {[0, 1, 2].map((i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="h-4 w-1/2" />
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
              </div>
            ))}
          </div>
        ) : query.isError ? (
          //  Ô NHẮC VIỆC mà tải hỏng thì không được nói "không có gì" — đó là trấn an giả.
          <p className="py-6 text-center text-sm text-muted-foreground">
            Không tải được lịch nhắc. Tải lại trang để thử lại.
          </p>
        ) : groups.length === 0 ? (
          <p className="py-6 text-center text-sm text-muted-foreground">
            Bạn chưa có quyền xem mục nhắc nào (sinh nhật cần quyền xem thông tin nhạy cảm, hợp đồng cần
            quyền xem hợp đồng lao động).
          </p>
        ) : (
          <div className={cn('grid gap-4', GRID_COLS[groups.length] ?? 'md:grid-cols-3')}>
            {groups.map((group) => (
              <ReminderGroup
                key={group.key}
                group={group}
                partial={group.key === 'expiring_contracts' && isPastContractLookahead(month, now)}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function ReminderGroup({ group, partial }: { group: MonthlyReminderGroup; partial: boolean }) {
  const Icon = GROUP_ICONS[group.key]
  const headingId = `monthly-reminder-${group.key}`
  return (
    <section aria-labelledby={headingId} className="min-w-0">
      <h3 id={headingId} className="mb-1 flex items-center gap-2 text-sm font-semibold">
        <Icon className="size-4 text-muted-foreground" aria-hidden />
        {group.title}
        <span className="rounded-full bg-muted px-2 text-xs font-medium tabular-nums text-muted-foreground">
          {group.total}
        </span>
      </h3>
      {group.rows.length === 0 ? (
        <p className="py-3 text-sm text-muted-foreground">Không có ai trong tháng này.</p>
      ) : (
        //  Tự cuộn: Tổng quan là chỗ liếc, không phải chỗ đọc 200 dòng.
        <ul className="max-h-72 divide-y overflow-y-auto">
          {group.rows.map((row) => (
            <ReminderRow key={row.id} group={group.key} row={row} />
          ))}
        </ul>
      )}
      {group.truncated && (
        <p className="pt-2 text-xs text-muted-foreground">
          Chỉ hiện {group.rows.length} trên {group.total} người — còn người khác chưa hiện.
        </p>
      )}
      {/*  Nguồn HĐ chỉ nhìn trước 180 ngày: tháng xa hơn thì "không có ai" chưa chắc đúng. */}
      {partial && (
        <p className="pt-2 text-xs text-muted-foreground">
          Chỉ thấy hợp đồng hết hạn trong {CONTRACT_LOOKAHEAD_DAYS} ngày tới — tháng này có thể còn thiếu.
        </p>
      )}
    </section>
  )
}

function ReminderRow({ group, row }: { group: MonthlyReminderGroupKey; row: MonthlyReminderRow }) {
  //  HĐ hết hạn mở thẳng tab hợp đồng — việc cần làm nằm ở đó (lập HĐ mới / chấm dứt).
  const to =
    group === 'expiring_contracts'
      ? `${appRoutes.hr.employeeDetail(row.employeeId)}?tab=labor-contracts`
      : appRoutes.hr.employeeDetail(row.employeeId)
  return (
    <li>
      <Link
        to={to}
        className="-mx-2 flex items-center justify-between gap-3 rounded-md px-2 py-2 transition-colors hover:bg-accent"
      >
        <div className="min-w-0">
          <p className="truncate text-sm font-medium">
            {row.employeeName}
            {row.employeeCode && <span className="font-normal text-muted-foreground"> · {row.employeeCode}</span>}
          </p>
          <p className={cn('truncate text-xs text-muted-foreground', row.urgent && 'text-destructive')}>
            {row.detail}
            {row.department ? ` · ${row.department}` : ''}
          </p>
        </div>
        <ChevronRight className="size-4 shrink-0 text-muted-foreground" aria-hidden />
      </Link>
    </li>
  )
}
