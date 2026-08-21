import { Badge } from '@/shared/ui/badge'
import { TONE_CLASS, type StatusTone } from '@/shared/ui/status-tone'
import { cn } from '@/shared/utils/cn'
import {
  PAYMENT_REQUEST_STATUS_LABELS,
  type PaymentRequestStatus,
} from '../types/payment-request'

/**
 * Màu trạng thái phiếu YCTT. Giữ đúng nghĩa của bản v1: nháp trung tính, chờ
 * duyệt vàng, đã duyệt / đã chi xanh, bị từ chối đỏ.
 */
const STATUS_TONE: Record<PaymentRequestStatus, StatusTone> = {
  draft: 'neutral',
  submitted: 'pending',
  approved: 'progress',
  paid: 'done',
  cancelled: 'danger',
}

export function PaymentRequestStatusBadge({ status }: { status: PaymentRequestStatus }) {
  if (!status) return <span className="text-muted-foreground">—</span>

  return (
    <Badge variant="secondary" className={cn('border-0', TONE_CLASS[STATUS_TONE[status] ?? 'neutral'])}>
      {PAYMENT_REQUEST_STATUS_LABELS[status] ?? status}
    </Badge>
  )
}
