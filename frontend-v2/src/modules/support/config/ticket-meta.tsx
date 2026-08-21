import { Badge } from '@/shared/ui/badge'
import { TONE_CLASS } from '@/shared/ui/status-tone'
import { cn } from '@/shared/utils/cn'
import {
  TICKET_PRIORITY_LABELS,
  TICKET_PRIORITY_TONE,
  TICKET_STATUS_LABELS,
  TICKET_STATUS_TONE,
} from './ticket-constants'

/** Huy hiệu trạng thái phiếu. Mã lạ thì hiện nguyên mã, tông trung tính. */
export function TicketStatusBadge({
  status,
  className,
}: {
  status: string
  className?: string
}) {
  if (!status) return <span className="text-muted-foreground">—</span>
  return (
    <Badge
      variant="secondary"
      className={cn('border-0', TONE_CLASS[TICKET_STATUS_TONE[status] ?? 'neutral'], className)}
    >
      {TICKET_STATUS_LABELS[status] ?? status}
    </Badge>
  )
}

/** Huy hiệu mức ưu tiên phiếu. */
export function TicketPriorityBadge({
  priority,
  className,
}: {
  priority: string
  className?: string
}) {
  if (!priority) return <span className="text-muted-foreground">—</span>
  return (
    <Badge
      variant="secondary"
      className={cn('border-0', TONE_CLASS[TICKET_PRIORITY_TONE[priority] ?? 'neutral'], className)}
    >
      {TICKET_PRIORITY_LABELS[priority] ?? priority}
    </Badge>
  )
}
