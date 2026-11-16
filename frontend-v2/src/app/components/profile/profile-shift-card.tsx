import { ChevronLeft, ChevronRight, Clock } from 'lucide-react'
import { useState } from 'react'

import { useMyWorkShifts } from '@/modules/hr/hooks/use-work-shifts'
import { appRoutes } from '@/shared/constants/app-routes'
import { useNotifications } from '@/shared/notifications/use-notifications'
import { addDays, startOfWeek, toISODate, WEEKDAY_LABELS } from '@/modules/hr/utils/calendar-grid'
import { describeMyShiftDay, type MyShiftTone } from '@/modules/hr/utils/my-shift-day'
import { parseISODate, todayInVietnamISO } from '@/modules/hr/utils/work-roster-range'
import { Button } from '@/shared/ui/button'
import { FormCard } from '@/shared/ui/form-card'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'

/** "2026-11-17" → "17/11". */
function shortDate(iso: string): string {
  return `${iso.slice(8, 10)}/${iso.slice(5, 7)}`
}

const TONE_CLASS: Record<MyShiftTone, string> = {
  //  Ca xếp riêng là NGOẠI LỆ → nổi màu ca (chữ trắng trên nền đậm); ngày thường lùi.
  shift: 'bg-shift text-shift-foreground',
  'shift-off': 'bg-shift text-shift-foreground',
  holiday: 'bg-destructive/10 text-destructive',
  off: 'text-muted-foreground',
  work: 'text-foreground',
}

/**
 * CA LÀM VIỆC của chính mình ở Trang cá nhân (duoc-CR-761, Q4): từng ngày trong tuần, giờ theo mẫu tuần hoặc ca xếp
 * riêng (ca xếp riêng thắng), ngày lễ, ngày nghỉ. Chuông "ca được xếp / đổi" mở về đây (`/me`).
 * Đọc `/api/work-shifts/me` — không cần khóa quyền, ai đăng nhập cũng xem được lịch của mình.
 */
export function ProfileShiftCard() {
  const todayISO = todayInVietnamISO()
  const thisMonday = toISODate(startOfWeek(parseISODate(todayISO) ?? new Date()))
  const [weekStart, setWeekStart] = useState(thisMonday)
  const monday = parseISODate(weekStart) ?? new Date()
  const weekEnd = toISODate(addDays(monday, 6))
  const shiftWeek = (step: number) => setWeekStart(toISODate(addDays(monday, step * 7)))

  //  Chuông "ca được xếp / đổi" (link `/me`) mới về → nạp lại thẻ. Dùng chung bộ nhớ đệm với cái chuông (cùng khóa,
  //  đã tự hỏi lại 20 giây) nên không thêm request nào.
  const { data: bell } = useNotifications(false)
  const shiftStamp = bell?.items?.find((n) => n.link === appRoutes.me)?.id ?? 0
  const { data, isPending, isError, isFetching } = useMyWorkShifts(weekStart, weekEnd, { refreshStamp: shiftStamp })
  const days = data?.days ?? []
  const isThisWeek = weekStart === thisMonday

  return (
    <FormCard
      title={isThisWeek ? 'Ca làm việc tuần này' : `Ca làm việc ${shortDate(weekStart)} – ${shortDate(weekEnd)}`}
      icon={Clock}
      iconClassName="text-muted-foreground"
      actions={
        <div className="flex items-center rounded-md border">
          <Button type="button" variant="ghost" size="icon-sm" className="rounded-r-none" aria-label="Tuần trước" onClick={() => shiftWeek(-1)}>
            <ChevronLeft className="size-4" />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="rounded-none border-x px-2"
            disabled={isThisWeek}
            onClick={() => setWeekStart(thisMonday)}
          >
            Tuần này
          </Button>
          <Button type="button" variant="ghost" size="icon-sm" className="rounded-l-none" aria-label="Tuần sau" onClick={() => shiftWeek(1)}>
            <ChevronRight className="size-4" />
          </Button>
        </div>
      }
    >
      {isPending ? (
        <div className="space-y-2">
          <Skeleton className="h-9 w-full" />
          <Skeleton className="h-9 w-full" />
          <Skeleton className="h-9 w-full" />
        </div>
      ) : isError ? (
        <p className="py-2 text-sm text-muted-foreground">Không tải được ca làm việc. Thử lại sau.</p>
      ) : days.length === 0 ? (
        <p className="py-2 text-sm text-muted-foreground">Tài khoản chưa gắn hồ sơ nhân sự nên chưa có lịch làm việc.</p>
      ) : (
        <ul className={cn('divide-y rounded-md border', isFetching && 'opacity-70 transition-opacity')}>
          {days.map((day) => {
            const view = describeMyShiftDay(day)
            const isToday = day.date === todayISO
            return (
              <li
                key={day.date}
                aria-current={isToday ? 'date' : undefined}
                className={cn('flex items-center gap-3 px-3 py-2 text-sm', isToday && 'bg-primary/5')}
              >
                <span className={cn('w-14 shrink-0 tabular-nums', isToday && 'font-semibold text-primary')}>
                  {WEEKDAY_LABELS[day.weekday] ?? ''} {shortDate(day.date)}
                </span>
                <span className="min-w-0 flex-1">
                  {/*  Mỗi khung một mảnh, thẻ hẹp thì xuống dòng giữa các khung — không cắt cụt giờ. */}
                  <span title={day.note || undefined} className="flex flex-wrap gap-1">
                    {view.parts.map((part, i) => (
                      <span
                        key={i}
                        className={cn('max-w-full truncate rounded-sm px-1.5 py-0.5 tabular-nums', TONE_CLASS[view.tone])}
                      >
                        {part}
                      </span>
                    ))}
                  </span>
                  {day.note && <span className="block truncate text-xs text-muted-foreground">{day.note}</span>}
                </span>
                <span className="shrink-0 text-right text-xs text-muted-foreground tabular-nums">
                  {view.hoursText}
                  {view.source && <span className="block max-w-28 truncate">{view.source}</span>}
                </span>
              </li>
            )
          })}
        </ul>
      )}
    </FormCard>
  )
}
