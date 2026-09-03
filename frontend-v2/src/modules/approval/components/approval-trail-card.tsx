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

/**
 * Mốc do CHỨNG TỪ tự thêm vào dòng thời gian, không phải mốc của bộ máy duyệt.
 *
 * Bộ máy chỉ ghi những gì nó làm ("đã rút trình duyệt"), nó không biết chứng từ
 * bên dưới ghi thêm gì vào sổ của mình — ví dụ lý do hủy mà người nộp gõ vào
 * `decision_note` của đơn nghỉ phép. Không có đường này thì mỗi phân hệ lại phải
 * dựng một dải cảnh báo riêng nằm ngoài dòng thời gian, đọc thành hai câu chuyện
 * rời nhau.
 */
export interface TrailExtraEvent {
  icon: LucideIcon
  /** Lớp màu cho vòng tròn mốc, cùng khuôn với `ACTION_APPEARANCE`. */
  iconClassName?: string
  title: string
  detail?: string
  time?: string | null
  /** Tô đỏ phần chữ — dành cho kết cục xấu. */
  emphasizeBad?: boolean
}

interface ApprovalTrailCardProps {
  instanceId: number
  /** Mốc của chứng từ, chèn lên ĐẦU danh sách (danh sách đọc mới nhất trước). */
  extraEvents?: TrailExtraEvent[]
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
export function ApprovalTrailCard({
  instanceId,
  extraEvents = [],
  className,
}: ApprovalTrailCardProps) {
  const { data, isLoading } = useApprovalTrail(instanceId)

  const instance = data?.instance
  const lines = data?.lines ?? []
  const tasks = data?.tasks ?? []
  const pending = tasks.filter((row) => row.status === TASK_STATUS.pending)
  //  Activity kiểu GitHub đọc từ HIỆN TẠI về quá khứ: việc cần xử lý nằm đầu,
  //  rồi mới tới thao tác mới nhất. API trả dấu vết cũ → mới cho bản in.
  const recentLines = lines.slice().reverse()

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

      {/*  KHÔNG dựng dải tóm tắt «Luồng xử lý · Người trình · Bắt đầu · Vị trí
           hiện tại» ở đây nữa (bỏ 03/09/2026). Bốn ô đó nói lại đúng những gì
           dòng thời gian ngay dưới đã nói, mà nói bằng từ của bộ máy nên người
           đọc phải dịch: mốc «đã bắt đầu trình duyệt» ở cuối danh sách vốn đã
           mang đủ người trình + thời điểm + tên luồng và số bản (backend ghi
           sẵn vào `comment`), «Vị trí hiện tại» thì trùng với mốc «Đang chờ
           phản hồi» nằm đầu danh sách, còn kết cục đã có huy hiệu ở tiêu đề. */}
      {!isLoading && instance && (
        <>
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
                    <p className="mt-0.5 break-words text-muted-foreground">
                      {instance.finish_reason ||
                        'Hệ thống chưa xác định được người xử lý tiếp theo.'}
                    </p>
                  </div>
                </div>
              )}

              {/*  Không đếm số mốc ở đây: con số trôi ra tận mép phải, không nói
                   thêm được gì mà chính danh sách ngay dưới không nói rõ hơn. */}
              <div className="mb-5 flex items-center gap-2">
                <h3 className="text-sm font-semibold">Hoạt động</h3>
                {/*  CHIỀU ĐỌC phải nói ra. Danh sách này đảo ngược (mới nhất
                     trên cùng) trong khi ô «Bắt đầu» ở dải tóm tắt lại là mốc
                     CŨ NHẤT — người đọc mặc định trên-xuống là xuôi thời gian
                     nên hiểu ngược toàn bộ trình tự ký. */}
                <Badge variant="outline" className="font-normal">
                  mới nhất trước
                </Badge>
              </div>

              {lines.length === 0 && pending.length === 0 && extraEvents.length === 0 ? (
                <p className="rounded-md border border-dashed px-4 py-6 text-center text-sm text-muted-foreground">
                  Chưa có thao tác nào.
                </p>
              ) : (
                <ol aria-label="Các mốc phê duyệt">
                  {extraEvents.map((event, index) => (
                    <ExtraEvent
                      key={event.title}
                      event={event}
                      showRail={
                        index < extraEvents.length - 1 ||
                        pending.length > 0 ||
                        recentLines.length > 0
                      }
                    />
                  ))}
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

/**
 * Sắc thái của phiên duyệt.
 *
 * ⚠️ **KHÔNG dùng `variant="default"` (nền `primary`) cho «Đã duyệt».** Nền
 * primary là navy — đúng màu nút hành động chính của cả bộ giao diện — nên huy
 * hiệu đọc ra như một cái nút bấm được nằm cạnh tiêu đề. Tô nền theo NGHĨA
 * (xanh lá = xong tốt) chứ không theo thang nhấn mạnh của bộ giao diện.
 *
 * ⚠️ Và không để bốn trạng thái còn lại chung một `outline` xám: «Đang chạy»,
 * «Trả về» và «Đã rút» là ba tình huống phải làm ba việc khác nhau.
 */
const INSTANCE_TONES: Partial<Record<number, string>> = {
  [INSTANCE_STATUS.running]:
    'border-sky-300 bg-sky-100 text-sky-800 dark:border-sky-700 dark:bg-sky-950 dark:text-sky-200',
  [INSTANCE_STATUS.approved]:
    'border-emerald-300 bg-emerald-100 text-emerald-800 dark:border-emerald-700 dark:bg-emerald-950 dark:text-emerald-200',
  [INSTANCE_STATUS.rejected]:
    'border-destructive/40 bg-destructive/15 text-destructive dark:bg-destructive/25',
  [INSTANCE_STATUS.returned]:
    'border-orange-300 bg-orange-100 text-orange-800 dark:border-orange-700 dark:bg-orange-950 dark:text-orange-200',
  [INSTANCE_STATUS.withdrawn]:
    'border-zinc-400 bg-zinc-200 text-zinc-700 dark:border-zinc-500 dark:bg-zinc-700 dark:text-zinc-200',
  [INSTANCE_STATUS.blocked]:
    'border-amber-400 bg-amber-100 text-amber-900 dark:border-amber-600 dark:bg-amber-950 dark:text-amber-200',
}

const INSTANCE_TONE_FALLBACK =
  'border-zinc-300 bg-zinc-100 text-zinc-600 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-300'

function InstanceStatus({ status, label }: { status: number; label: string }) {
  return (
    <Badge
      variant="outline"
      className={cn('font-medium', INSTANCE_TONES[status] ?? INSTANCE_TONE_FALLBACK)}
    >
      {label}
    </Badge>
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
        {/*  Giờ đi LIỀN sau câu, không đẩy sang mép phải bằng `justify-between`:
             thẻ chạy hết bề ngang màn 24" nên mốc thời gian trôi ra tận đầu kia,
             rời hẳn khỏi dòng nó nói về, mắt phải bắc cầu qua một khoảng trống
             dài cả gang tay. */}
        <p className="min-w-0 text-sm leading-5">
          <span className="font-semibold text-foreground">{actorName}</span>{' '}
          <span className="font-semibold text-foreground">{actionPhrase(line)}</span>
          <time
            dateTime={line.created_at}
            className="ml-2 text-xs font-normal text-muted-foreground tabular-nums"
          >
            {formatDateTime(line.created_at)}
          </time>
        </p>

        {/*  `break-words` KHÔNG được bỏ. Ý kiến là chữ người dùng gõ tự do và
             có thật những chuỗi vài trăm ký tự không một dấu cách (lý do dán
             từ chỗ khác, mã phiếu nối nhau). `whitespace-pre-wrap` một mình chỉ
             xuống dòng ở chỗ CÓ khoảng trắng, nên chuỗi liền chạy thẳng ra
             ngoài thẻ: đo được 3139px nội dung trong khung 768px, đè lên cột
             bên cạnh và sinh thanh cuộn ngang cho cả trang (dựng lại được trên
             giao diện thật 03/09/2026 với lý do hủy 420 ký tự). */}
        {line.comment && (
          <p className="mt-1 max-w-3xl text-sm leading-5 break-words whitespace-pre-wrap text-muted-foreground">
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

/** Mốc của CHỨNG TỪ — cùng khuôn với mốc của bộ máy để đọc thành một mạch. */
function ExtraEvent({ event, showRail }: { event: TrailExtraEvent; showRail: boolean }) {
  const Icon = event.icon

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
        className={cn(
          'relative z-10 grid size-8 shrink-0 place-items-center rounded-full border print:bg-background',
          event.iconClassName ?? DEFAULT_ACTION_APPEARANCE.iconClassName,
        )}
        aria-hidden="true"
      >
        <Icon className="size-4" strokeWidth={2.25} />
      </span>

      <article className="min-w-0 flex-1 pt-1" aria-label={event.title}>
        <p className="min-w-0 text-sm leading-5">
          <span
            className={cn(
              'font-semibold',
              event.emphasizeBad ? 'text-destructive' : 'text-foreground',
            )}
          >
            {event.title}
          </span>
          {event.time && (
            <time
              dateTime={event.time}
              className="ml-2 text-xs font-normal text-muted-foreground tabular-nums"
            >
              {formatDateTime(event.time)}
            </time>
          )}
        </p>

        {event.detail && (
          <p className="mt-1 max-w-3xl text-sm leading-5 whitespace-pre-wrap break-words text-muted-foreground">
            {event.detail}
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
