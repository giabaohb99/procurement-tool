import { CheckCircle2, History, Loader2, Users } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'
import { formatDateTime, formatTime } from '@/shared/utils/format-date'
import { ActivityFilterBar } from './activity-filter-bar'
import { useWorkActivities, useWorkActivityActors } from '../hooks/use-work-activities'
import { WORK_ACTIVITY_KIND, type WorkActivity, type WorkActivityKind } from '../types/activity'
import { describeActivity } from '../utils/describe-activity'
import { groupActivitiesByDay } from '../utils/group-activities-by-day'
import { initials } from '../utils/people'

interface ActivityFeedProps {
  listId: number
  /** Bấm vào dòng có gắn việc thì mở panel chi tiết việc đó. */
  onOpenTask: (taskId: number) => void
}

/**
 * Tab «Hoạt động» — dòng thời gian gộp của cả dự án (D-09, §8 của
 * `05-giao-dien.md`), dựng theo đúng khuôn *Activities* của Lark.
 *
 * Bố cục một cụm ngày, TRẢI HẾT bề ngang:
 *
 * ```
 * Hôm nay   ────────────────────────────────────────────────────
 *   31      14:05  (av)  ✔ Tên việc                       ← chữ nhỏ, xám
 *                        Dego Admin đã sửa công việc      ← câu kể, chữ đậm
 * ```
 *
 * - Cột ngày nằm NGOÀI cùng bên trái và DÍNH khi cuộn: nhật ký dài hàng trăm
 *   dòng, cuộn giữa chừng mà không biết đang ở ngày nào thì cột giờ vô nghĩa.
 * - Giờ đứng riêng một cột hẹp, canh phải — mọi dòng thẳng hàng thì mắt dò
 *   xuống theo cột giờ được, còn nhét giờ vào cuối câu là mỗi dòng một chỗ.
 * - Tên việc ở dòng TRÊN, câu kể ở dòng dưới — nên câu kể đã bỏ cái đuôi lặp
 *   tên việc (xem `describeActivity`).
 *
 * Không dùng `DataTable`: đây không phải bảng — không cột sắp xếp được, không
 * chọn dòng, và dài vô hạn theo kiểu bảng tin.
 */
export function ActivityFeed({ listId, onOpenTask }: ActivityFeedProps) {
  const [kind, setKind] = useState<WorkActivityKind | null>(null)
  const [by, setBy] = useState<number | null>(null)

  const { data, isLoading, isError, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useWorkActivities(listId, { kind, by })
  const { data: actors = [] } = useWorkActivityActors(listId)

  const items = data?.pages.flatMap((p) => p.items) ?? []
  const total = data?.pages[0]?.total ?? 0
  const days = groupActivitiesByDay(items)

  return (
    //  Hàng lọc nằm NGOÀI khung cuộn: nó là thanh công cụ của tab này, cuộn
    //  xuống dòng thứ hai trăm mà muốn đổi bộ lọc thì phải cuộn ngược lên đầu.
    <div className="flex min-h-0 flex-1 flex-col">
      <ActivityFilterBar
        kind={kind}
        onKindChange={setKind}
        by={by}
        onByChange={setBy}
        actors={actors}
        total={total}
      />

      <div className="min-h-0 flex-1 overflow-y-auto">
        {isLoading && (
          <div className="space-y-3 pt-6">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        )}

        {isError && !isLoading && (
          <p className="py-10 text-center text-sm text-muted-foreground">
            Không đọc được dòng hoạt động của dự án này.
          </p>
        )}

        {!isLoading && !isError && items.length === 0 && (
          <div className="flex flex-col items-center gap-2 py-16 text-muted-foreground">
            <History className="size-8" />
            <p className="text-sm">
              {kind !== null || by !== null
                ? 'Không có hoạt động nào khớp bộ lọc.'
                : 'Chưa có hoạt động nào.'}
            </p>
          </div>
        )}

        {days.map((day) => (
          <section key={day.key || 'khong-ro'} className="flex gap-4 pt-6">
            <div className="sticky top-0 w-14 shrink-0 self-start pt-1 text-muted-foreground">
              <div className="text-xs leading-tight">{day.label}</div>
              {day.dayNumber && (
                <div className="text-2xl leading-tight font-semibold text-foreground">
                  {day.dayNumber}
                </div>
              )}
            </div>

            <div className="min-w-0 flex-1 border-t pt-1">
              <ol>
                {day.items.map((item) => (
                  <ActivityRow key={item.id} activity={item} onOpenTask={onOpenTask} />
                ))}
              </ol>
            </div>
          </section>
        ))}

        {hasNextPage && (
          <div className="py-6 text-center">
            <Button
              variant="outline"
              size="sm"
              disabled={isFetchingNextPage}
              onClick={() => void fetchNextPage()}
            >
              {isFetchingNextPage && <Loader2 className="size-4 animate-spin" />}
              Xem thêm hoạt động
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * Một dòng: giờ · avatar chữ tắt · tên việc (nhỏ, xám) · câu kể (đậm).
 *
 * Cả dòng là vùng bấm khi có việc gắn kèm — Lark cũng vậy, và bôi sáng cả dải
 * ngang khi rê chuột thì mắt bám được một dòng dài suốt bề ngang màn hình.
 * Dòng KHÔNG gắn việc (mời thành viên, xếp lại cột) thì không bấm được: dựng
 * `<button>` rỗng chỉ để nó nhấp nháy là lừa người dùng.
 */
function ActivityRow({
  activity,
  onOpenTask,
}: {
  activity: WorkActivity
  onOpenTask: (taskId: number) => void
}) {
  const taskId = activity.task_id
  const clickable = taskId !== null && Boolean(activity.task_title)

  return (
    <li>
      <div
        role={clickable ? 'button' : undefined}
        tabIndex={clickable ? 0 : undefined}
        onClick={clickable ? () => onOpenTask(taskId) : undefined}
        onKeyDown={
          clickable
            ? (su) => {
                if (su.key === 'Enter' || su.key === ' ') {
                  su.preventDefault()
                  onOpenTask(taskId)
                }
              }
            : undefined
        }
        className={cn(
          'flex items-start gap-3 rounded-md px-3 py-2.5 text-left',
          clickable && 'cursor-pointer hover:bg-accent/60 focus-visible:bg-accent/60',
          clickable && 'outline-none focus-visible:ring-2 focus-visible:ring-ring/50',
        )}
      >
        <time
          className="w-12 shrink-0 pt-0.5 text-right text-xs text-muted-foreground tabular-nums"
          title={formatDateTime(activity.at)}
        >
          {formatTime(activity.at)}
        </time>

        <span
          aria-hidden
          className={cn(
            'grid size-7 shrink-0 place-items-center rounded-full border text-[10px] font-medium',
            kindTone(activity.kind),
          )}
        >
          {initials(activity.by)}
        </span>

        <div className="min-w-0 flex-1">
          {/*  Dòng nhỏ phía trên = ĐỐI TƯỢNG bị tác động: tên việc, hoặc tên
              loại sự kiện khi dòng không gắn với việc nào. */}
          <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <KindIcon kind={activity.kind} />
            <span className="truncate">{activity.task_title || kindName(activity.kind)}</span>
          </p>
          <p className="text-sm leading-snug font-medium text-foreground">
            {activity.by} {describeActivity(activity)}
          </p>
        </div>
      </div>
    </li>
  )
}

/** Nhãn thay cho tên việc ở dòng nhỏ, khi sự kiện không gắn với việc nào. */
function kindName(kind: number): string {
  if (kind === WORK_ACTIVITY_KIND.MEMBER) return 'Thành viên dự án'
  if (kind === WORK_ACTIVITY_KIND.LIST) return 'Dự án & cột'
  return 'Công việc'
}

/**
 * Biểu tượng đứng trước tên đối tượng.
 *
 * Là một component chứ không phải hàm trả về *kiểu* component: gán
 * `const Icon = kindIcon(...)` ngay trong thân dòng là "tạo component lúc
 * render" — React coi mỗi lần render là một loại khác nhau và dựng lại cây con.
 */
function KindIcon({ kind }: { kind: number }) {
  const Icon = kind === WORK_ACTIVITY_KIND.MEMBER ? Users : CheckCircle2
  return <Icon className="size-3.5 shrink-0" />
}

/** Màu viền/nền avatar theo LOẠI sự kiện — liếc là biết cụm nào là cụm nào. */
function kindTone(kind: number): string {
  if (kind === WORK_ACTIVITY_KIND.MEMBER)
    return 'border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-400'
  if (kind === WORK_ACTIVITY_KIND.LIST)
    return 'border-sky-500/30 bg-sky-500/10 text-sky-700 dark:text-sky-400'
  return 'bg-accent text-accent-foreground'
}
