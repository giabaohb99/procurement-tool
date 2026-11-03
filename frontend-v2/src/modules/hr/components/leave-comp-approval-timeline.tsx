import { Ban, Check, FileText, Hourglass, Undo2, X, type LucideIcon } from 'lucide-react'

import {
  ApprovalTrailCard,
  type TrailExtraEvent,
} from '@/modules/approval/components/approval-trail-card'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { cn } from '@/shared/utils/cn'
import { formatDateTime } from '@/shared/utils/format-date'
import { LEAVE_COMP_STATUS, type LeaveCompRequest } from '../types/leave-comp'

interface LeaveCompApprovalTimelineProps {
  request: LeaveCompRequest
}

const OUTCOME: Record<number, { icon: LucideIcon; title: string; bad: boolean }> = {
  [LEAVE_COMP_STATUS.APPROVED]: { icon: Check, title: 'Phiếu đã được duyệt', bad: false },
  [LEAVE_COMP_STATUS.REJECTED]: { icon: X, title: 'Phiếu bị từ chối', bad: true },
  [LEAVE_COMP_STATUS.RETURNED]: { icon: Undo2, title: 'Phiếu bị trả về để chỉnh sửa', bad: true },
  [LEAVE_COMP_STATUS.CANCELLED]: { icon: Ban, title: 'Phiếu đã bị hủy', bad: true },
}

function createdEvent(request: LeaveCompRequest): TrailExtraEvent {
  const actor = request.created_by_name?.trim()
  return {
    icon: FileText,
    iconClassName: 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40',
    title: actor ? `${actor} đã lập phiếu` : 'Lập phiếu',
    detail: `Số phiếu ${request.code}`,
    time: request.created_at,
  }
}

/**
 * Luồng duyệt của phiếu nghỉ bù.
 *  · Có phiên duyệt (`approval_instance_id > 0`) → `ApprovalTrailCard` của phân hệ Phê duyệt (dấu vết thật),
 *    chèn thêm mốc "lập phiếu" ở đáy và — riêng phiếu HỦY — mốc kết cục ở đầu, vì bộ máy chỉ biết "đã rút".
 *  · Duyệt thẳng → ba mốc dựng từ chính phiếu: lập · chờ/kết quả (kèm ghi chú của người chốt).
 */
export function LeaveCompApprovalTimeline({ request }: LeaveCompApprovalTimelineProps) {
  const outcome = OUTCOME[request.status]
  const note = request.decision_note?.trim()

  if (request.approval_instance_id > 0) {
    const extra: TrailExtraEvent[] =
      request.status === LEAVE_COMP_STATUS.CANCELLED && outcome
        ? [
            {
              icon: outcome.icon,
              iconClassName: 'border-destructive/30 bg-destructive/5 text-destructive',
              title: outcome.title,
              detail: note ? `Lý do: ${note}` : undefined,
              time: request.decided_at,
              emphasizeBad: true,
            },
          ]
        : []
    return (
      <ApprovalTrailCard
        instanceId={request.approval_instance_id}
        extraEvents={extra.length ? extra : undefined}
        trailingEvents={[createdEvent(request)]}
        hidePrint
      />
    )
  }

  const steps: { key: string; icon: LucideIcon; title: string; detail?: string; time?: string | null; tone: string }[] = [
    {
      key: 'created',
      icon: FileText,
      title: request.created_by_name?.trim()
        ? `${request.created_by_name.trim()} đã lập phiếu`
        : 'Lập phiếu',
      detail: `Số phiếu ${request.code}`,
      time: request.created_at,
      tone: 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40',
    },
    outcome
      ? {
          key: 'outcome',
          icon: outcome.icon,
          title: outcome.title,
          detail: note ? (outcome.bad ? `Lý do: ${note}` : note) : undefined,
          time: request.decided_at,
          tone: outcome.bad
            ? 'border-destructive/30 bg-destructive/5 text-destructive'
            : 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40',
        }
      : {
          key: 'waiting',
          icon: Hourglass,
          title:
            request.status === LEAVE_COMP_STATUS.PENDING ? 'Đang chờ duyệt' : 'Chưa gửi duyệt',
          detail:
            request.status === LEAVE_COMP_STATUS.PENDING
              ? undefined
              : 'Bấm "Gửi duyệt" khi đã nhập đủ.',
          tone:
            request.status === LEAVE_COMP_STATUS.PENDING
              ? 'border-sky-200 bg-sky-50 text-sky-700 dark:bg-sky-950/40'
              : 'border-border bg-background text-muted-foreground',
        },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Luồng duyệt</CardTitle>
      </CardHeader>
      <CardContent>
        <ol className="space-y-3">
          {steps.map((s) => (
            <li key={s.key} className="flex gap-3">
              <span
                className={cn(
                  'flex size-8 shrink-0 items-center justify-center rounded-full border',
                  s.tone,
                )}
              >
                <s.icon className="size-4" />
              </span>
              <div className="min-w-0 text-sm">
                <p className="font-medium break-words">{s.title}</p>
                {s.time && (
                  <p className="text-xs text-muted-foreground">{formatDateTime(s.time)}</p>
                )}
                {s.detail && (
                  <p className="text-muted-foreground break-words whitespace-pre-wrap">{s.detail}</p>
                )}
              </div>
            </li>
          ))}
        </ol>
      </CardContent>
    </Card>
  )
}
