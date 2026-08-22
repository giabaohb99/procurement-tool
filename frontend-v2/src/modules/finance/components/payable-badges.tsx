import { Badge } from '@/shared/ui/badge'
import { TONE_CLASS, type StatusTone } from '@/shared/ui/status-tone'
import { cn } from '@/shared/utils/cn'
import { agingLabel, payableStatusLabel } from '../types/payable'

/** Màu theo MÃ trạng thái (B-05). Mã lạ rơi về `neutral` chứ không mất badge. */
const STATUS_TONE: Record<string, StatusTone> = {
  unpaid: 'neutral',
  partial: 'pending',
  paid: 'done',
}

export function PayableStatusBadge({ status }: { status: string }) {
  if (!status) return <span className="text-muted-foreground">—</span>

  return (
    <Badge variant="secondary" className={cn('border-0', TONE_CLASS[STATUS_TONE[status] ?? 'neutral'])}>
      {payableStatusLabel(status)}
    </Badge>
  )
}

/**
 * Tuổi nợ. Quá 60 ngày mới chuyển đỏ — giữ đúng ngưỡng của bản v1 để người dùng
 * cũ không phải học lại: dưới 60 là "nhắc", trên 60 là "phải xử lý ngay".
 */
const AGING_TONE: Record<string, StatusTone> = {
  'Chưa đến hạn': 'neutral',
  '1-30': 'pending',
  '31-60': 'pending',
  '61-90': 'danger',
  '>90': 'danger',
}

export function PayableAgingBadge({ aging }: { aging: string }) {
  if (!aging) return <span className="text-muted-foreground">—</span>

  return (
    <Badge variant="secondary" className={cn('border-0', TONE_CLASS[AGING_TONE[aging] ?? 'neutral'])}>
      {agingLabel(aging)}
    </Badge>
  )
}
