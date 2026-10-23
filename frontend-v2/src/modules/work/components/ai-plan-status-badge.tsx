import { Badge } from '@/shared/ui/badge'
import { cn } from '@/shared/utils/cn'
import { AI_PLAN_STATUS_APPROVED, AI_PLAN_STATUS_PENDING } from '../types/ai-plan'

interface AiPlanStatusBadgeProps {
  status: number
  label: string
  className?: string
}

/** Chờ duyệt = vàng (còn việc của bạn) · Đã duyệt = xanh · còn lại (từ chối, hủy, tạo thẳng) = xám. */
export function AiPlanStatusBadge({ status, label, className }: AiPlanStatusBadgeProps) {
  return (
    <Badge
      variant="secondary"
      className={cn(
        'border-0',
        status === AI_PLAN_STATUS_PENDING && 'bg-warning/10 text-warning',
        status === AI_PLAN_STATUS_APPROVED && 'bg-success/10 text-success',
        className,
      )}
    >
      {label}
    </Badge>
  )
}
