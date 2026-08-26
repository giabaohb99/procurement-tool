import type { LucideIcon } from 'lucide-react'
import {
  AlertTriangle,
  ArrowUp,
  Check,
  CircleDot,
  Clock3,
  FastForward,
  Flag,
  MessageSquareText,
  Play,
  Printer,
  RotateCcw,
  ShieldCheck,
  Undo2,
  UsersRound,
  X,
} from 'lucide-react'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'
import { formatDateTime } from '@/shared/utils/format-date'
import { useApprovalTrail } from '../hooks/use-approvals'
import {
  ACTION,
  INSTANCE_STATUS,
  TASK_STATUS,
  type ApprovalAction,
  type ApprovalTask,
} from '../types/approval'

interface ApprovalTrailCardProps {
  instanceId: number
  className?: string
}

interface ActionAppearance {
  icon: LucideIcon
  iconClassName: string
}

const DEFAULT_ACTION_APPEARANCE: ActionAppearance = {
  icon: CircleDot,
  iconClassName: 'border-border bg-background text-muted-foreground',
}

const ACTION_APPEARANCE: Partial<Record<number, ActionAppearance>> = {
  [ACTION.start]: {
    icon: Play,
    iconClassName: 'border-sky-200 bg-sky-50 text-sky-700',
  },
  [ACTION.approve]: {
    icon: Check,
    iconClassName: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  },
  [ACTION.reject]: {
    icon: X,
    iconClassName: 'border-destructive/30 bg-destructive/5 text-destructive',
  },
  [ACTION.return]: {
    icon: Undo2,
    iconClassName: 'border-amber-200 bg-amber-50 text-amber-700',
  },
  [ACTION.withdraw]: {
    icon: RotateCcw,
    iconClassName: 'border-rose-200 bg-rose-50 text-rose-700',
  },
  [ACTION.skipDuplicate]: {
    icon: FastForward,
    iconClassName: 'border-violet-200 bg-violet-50 text-violet-700',
  },
  [ACTION.reassign]: {
    icon: UsersRound,
    iconClassName: 'border-indigo-200 bg-indigo-50 text-indigo-700',
  },
  [ACTION.comment]: {
    icon: MessageSquareText,
    iconClassName: 'border-border bg-muted text-muted-foreground',
  },
  [ACTION.escalate]: {
    icon: ArrowUp,
    iconClassName: 'border-orange-200 bg-orange-50 text-orange-700',
  },
  [ACTION.finish]: {
    icon: Flag,
    iconClassName: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  },
}

/**
 * LỊCH SỬ PHÊ DUYỆT (I20): timeline kiểm toán dùng chung cho mọi chứng từ.
 *
 * Backend vẫn cấp `sentence` làm câu chuẩn cho bản in/xuất. Trên màn hình, các
 * thành phần của cùng một câu được tách ra để người đọc quét nhanh người làm,
 * hành động, chặng, ủy quyền, ý kiến và thời điểm mà không phải đọc một đoạn dài.
 */
export function ApprovalTrailCard({ instanceId, className }: ApprovalTrailCardProps) {
  const { data, isLoading } = useApprovalTrail(instanceId)

  const instance = data?.instance
  const lines = data?.lines ?? []
  const tasks = data?.tasks ?? []
  const pending = tasks.filter((row) => row.status === TASK_STATUS.pending)
  //  Activity kiểu GitHub đọc từ HIỆN TẠI về quá khứ: việc cần xử lý nằm đầu,
  //  rồi mới tới thao tác mới nhất. API trả dấu vết cũ → mới cho bản in.
  const recentLines = lines.slice().reverse()
  const currentStepName =
    pending[0]?.node_name ||
    lines
      .slice()
      .reverse()
      .find((line) => line.node_seq === instance?.current_seq)?.node_name ||
    ''

  return (
    <Card className={cn('gap-0 py-0 print:border-0 print:shadow-none', className)}>
      <CardHeader className="flex min-h-16 flex-row items-center justify-between gap-4 border-b px-5 py-4">
        <CardTitle className="flex min-w-0 items-center gap-2.5 text-base">
          <span className="grid size-8 shrink-0 place-items-center rounded-md border bg-muted/40">
            <ShieldCheck className="size-4 text-muted-foreground" />
          </span>
          <span className="truncate">Lịch sử phê duyệt</span>
          {instance && <InstanceStatus status={instance.status} label={instance.status_label} />}
        </CardTitle>

        <Button
          type="button"
          variant="outline"
          size="sm"
          className="shrink-0 print:hidden"
          aria-label="In lịch sử phê duyệt"
          onClick={() => window.print()}
        >
          <Printer className="size-4" />
          In
        </Button>
      </CardHeader>

      {isLoading && (
        <CardContent className="space-y-4 px-5 py-5">
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-32 w-full" />
        </CardContent>
      )}

      {!isLoading && instance && (
        <>
          <dl className="grid border-b bg-muted/15 sm:grid-cols-2 xl:grid-cols-4 xl:[&>div]:border-l xl:[&>div:first-child]:border-l-0 sm:[&>div:nth-child(even)]:border-l sm:[&>div:nth-child(n+3)]:border-b-0">
            <SummaryItem label="Luồng xử lý">
              <span className="block truncate" title={instance.flow_name}>
                {instance.flow_name || 'Luồng không tên'}
              </span>
              <span className="mt-0.5 block text-xs font-normal text-muted-foreground">
                Phiên bản {instance.flow_version}
              </span>
            </SummaryItem>
            <SummaryItem label="Người trình">{instance.started_by_name || 'Hệ thống'}</SummaryItem>
            <SummaryItem label="Bắt đầu">
              <time dateTime={instance.started_at ?? undefined} className="tabular-nums">
                {formatDateTime(instance.started_at) || 'Chưa ghi nhận'}
              </time>
            </SummaryItem>
            <SummaryItem label="Vị trí hiện tại" isLast>
              {instance.finished_at ? (
                <>
                  Đã kết thúc
                  <span className="mt-0.5 block text-xs font-normal text-muted-foreground">
                    {formatDateTime(instance.finished_at)}
                  </span>
                </>
              ) : instance.current_seq > 0 ? (
                <>
                  Chặng {instance.current_seq}
                  {currentStepName && (
                    <span className="mt-0.5 block truncate text-xs font-normal text-muted-foreground">
                      {currentStepName}
                    </span>
                  )}
                </>
              ) : (
                'Chưa xác định'
              )}
            </SummaryItem>
          </dl>

          <CardContent className="px-5 py-5">
            <div className="max-w-6xl">
              {instance.status === INSTANCE_STATUS.blocked && (
                <div
                  role="alert"
                  className="mb-5 flex gap-3 rounded-md border border-destructive/30 bg-destructive/5 px-3.5 py-3 text-sm"
                >
                  <AlertTriangle className="mt-0.5 size-4 shrink-0 text-destructive" />
                  <div>
                    <p className="font-semibold text-destructive">Luồng đang bị kẹt</p>
                    <p className="mt-0.5 text-muted-foreground">
                      {instance.finish_reason ||
                        'Hệ thống chưa xác định được người xử lý tiếp theo.'}
                    </p>
                  </div>
                </div>
              )}

              <div className="mb-5 flex flex-wrap items-center justify-between gap-x-3 gap-y-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-semibold">Hoạt động</h3>
                  {/*  CHIỀU ĐỌC phải nói ra. Danh sách này đảo ngược (mới nhất
                       trên cùng) trong khi ô «Bắt đầu» ở dải tóm tắt lại là mốc
                       CŨ NHẤT — người đọc mặc định trên-xuống là xuôi thời gian
                       nên hiểu ngược toàn bộ trình tự ký. */}
                  <Badge variant="outline" className="font-normal">
                    mới nhất trước
                  </Badge>
                </div>
                <span className="text-xs text-muted-foreground tabular-nums">
                  {lines.length} mốc đã ghi nhận
                </span>
              </div>

              {lines.length === 0 && pending.length === 0 ? (
                <p className="rounded-md border border-dashed px-4 py-6 text-center text-sm text-muted-foreground">
                  Chưa có thao tác nào.
                </p>
              ) : (
                <ol aria-label="Các mốc phê duyệt">
                  {pending.length > 0 && (
                    <PendingEvent tasks={pending} showRail={recentLines.length > 0} />
                  )}
                  {recentLines.map((line, index) => (
                    <ApprovalEvent
                      key={line.id}
                      line={line}
                      showRail={index < recentLines.length - 1}
                    />
                  ))}
                </ol>
              )}
            </div>
          </CardContent>
        </>
      )}
    </Card>
  )
}

function InstanceStatus({ status, label }: { status: number; label: string }) {
  return (
    <Badge
      variant={
        status === INSTANCE_STATUS.approved
          ? 'default'
          : status === INSTANCE_STATUS.blocked || status === INSTANCE_STATUS.rejected
            ? 'destructive'
            : 'outline'
      }
      className="font-medium"
    >
      {label}
    </Badge>
  )
}

function SummaryItem({
  label,
  children,
  isLast = false,
}: {
  label: string
  children: React.ReactNode
  isLast?: boolean
}) {
  return (
    <div className={cn('min-w-0 border-b px-5 py-5 xl:border-b-0', isLast && 'border-b-0')}>
      <dt className="text-xs leading-5 font-medium text-muted-foreground">{label}</dt>
      <dd className="mt-1.5 min-w-0 text-sm leading-5 font-semibold">{children}</dd>
    </div>
  )
}

function ApprovalEvent({ line, showRail }: { line: ApprovalAction; showRail: boolean }) {
  const appearance = ACTION_APPEARANCE[line.action] ?? DEFAULT_ACTION_APPEARANCE
  const Icon = appearance.icon
  const actorName = line.actor_name || 'Hệ thống'
  const isMinorSystemEvent = !line.actor_name && line.action === ACTION.approve

  return (
    <li className="relative flex gap-4 pb-7 last:pb-0">
      {showRail && (
        <span
          data-testid="approval-timeline-rail"
          aria-hidden="true"
          className="approval-timeline-rail print:bg-slate-400"
        />
      )}
      {isMinorSystemEvent ? (
        <span className="relative z-10 grid size-8 shrink-0 place-items-center" aria-hidden="true">
          <span className="approval-timeline-system-node ring-4 ring-background" />
        </span>
      ) : (
        <span
          className={cn(
            'relative z-10 grid size-8 shrink-0 place-items-center rounded-full border print:bg-background',
            appearance.iconClassName,
          )}
          aria-hidden="true"
        >
          <Icon className="size-4" strokeWidth={2.25} />
        </span>
      )}

      <article className="min-w-0 flex-1 pt-1" aria-label={`${actorName} ${actionPhrase(line)}`}>
        <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between sm:gap-4">
          <p className="min-w-0 text-sm leading-5">
            <span className="font-semibold text-foreground">{actorName}</span>{' '}
            <span className="font-semibold text-foreground">{actionPhrase(line)}</span>
          </p>
          <time
            dateTime={line.created_at}
            className="shrink-0 text-xs text-muted-foreground tabular-nums"
          >
            {formatDateTime(line.created_at)}
          </time>
        </div>

        {line.comment && (
          <p className="mt-1 max-w-3xl text-sm leading-5 whitespace-pre-wrap text-muted-foreground">
            {line.comment}
          </p>
        )}

        {/*  Chặng để thành huy hiệu: đây là thứ nối mốc này với thẻ «Luồng» ở
             trên, mà chữ mờ 12px thì lẫn mất giữa ý kiến và dòng ủy quyền. */}
        {(line.node_seq > 0 || line.node_name) && (
          <p className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted-foreground">
            {line.node_seq > 0 && (
              <Badge variant="outline" className="font-normal">
                Chặng {line.node_seq}
              </Badge>
            )}
            {line.node_name}
          </p>
        )}

        {line.on_behalf_of_name && (
          <p className="mt-1 text-xs text-muted-foreground">
            Thực hiện thay{' '}
            <span className="font-medium text-foreground">{line.on_behalf_of_name}</span>
            {line.delegation_id && ` · Theo ủy quyền #${line.delegation_id}`}
          </p>
        )}
      </article>
    </li>
  )
}

function PendingEvent({ tasks, showRail }: { tasks: ApprovalTask[]; showRail: boolean }) {
  return (
    <li className="relative flex gap-4 pb-7 last:pb-0">
      {showRail && (
        <span
          data-testid="approval-timeline-rail"
          aria-hidden="true"
          className="approval-timeline-rail print:bg-slate-400"
        />
      )}
      <span
        className="relative z-10 grid size-8 shrink-0 place-items-center rounded-full border border-sky-200 bg-sky-50 text-sky-700 print:bg-background"
        aria-hidden="true"
      >
        <Clock3 className="size-4" strokeWidth={2.25} />
      </span>

      <section className="min-w-0 flex-1 pt-1" aria-label="Đang chờ phản hồi">
        <h4 className="text-sm font-semibold">Đang chờ phản hồi</h4>
        <ul className="mt-1 max-w-3xl space-y-1.5">
          {tasks.map((task) => (
            <li key={task.id} className="text-sm leading-5 text-muted-foreground">
              <span className="font-medium text-foreground">
                {task.assignee_name || 'Chưa xác định người duyệt'}
              </span>
              <span aria-hidden="true"> · </span>
              <span>Chặng {task.node_seq}</span>
              {task.node_name && `: ${task.node_name}`}
              <span aria-hidden="true"> · </span>
              {task.due_at ? (
                <>
                  Hạn xử lý:{' '}
                  <time dateTime={task.due_at} className="tabular-nums">
                    {formatDateTime(task.due_at)}
                  </time>
                </>
              ) : (
                'Chưa đặt hạn xử lý'
              )}
              {tasks.length > 1 && ` · Thứ tự ${task.order_no}`}
            </li>
          ))}
        </ul>
      </section>
    </li>
  )
}

function actionPhrase(line: ApprovalAction): string {
  //  Sự kiện do máy tạo không được đọc thành “Hệ thống đã duyệt”, vì máy chỉ
  //  đang mở/chuyển bước chứ không chịu trách nhiệm phê duyệt thay con người.
  if (!line.actor_name && line.action === ACTION.approve) return 'đã cập nhật bước xử lý'

  const phrases: Partial<Record<number, string>> = {
    [ACTION.start]: 'đã bắt đầu trình duyệt',
    [ACTION.approve]: 'đã duyệt',
    [ACTION.reject]: 'đã từ chối',
    [ACTION.return]: 'đã trả lại',
    [ACTION.withdraw]: 'đã rút trình duyệt',
    [ACTION.skipDuplicate]: 'đã tự động chuyển qua vì trùng người duyệt',
    [ACTION.reassign]: 'đã chuyển người xử lý',
    [ACTION.comment]: 'đã thêm ý kiến',
    [ACTION.escalate]: 'đã chuyển lên cấp trên do quá hạn',
    [ACTION.finish]: 'đã kết thúc luồng',
  }
  return phrases[line.action] ?? `đã thực hiện ${line.action_label.toLocaleLowerCase('vi-VN')}`
}
