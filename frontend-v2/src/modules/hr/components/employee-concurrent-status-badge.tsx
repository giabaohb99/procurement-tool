import { Badge } from '@/shared/ui/badge'
import { TONE_CLASS } from '@/shared/ui/status-tone'
import { cn } from '@/shared/utils/cn'
import type { EmployeeConcurrent } from '../types/employee-concurrent'
import { concurrentStatusLabel, concurrentStatusTone } from '../utils/employee-concurrent-display'

interface EmployeeConcurrentStatusBadgeProps {
  row: Pick<EmployeeConcurrent, 'status' | 'status_label'>
  className?: string
}

/** Huy hiệu Sắp tới / Đang hiệu lực / Đã hết — nhãn từ backend hoặc bộ mã sinh `CONCURRENT_STATUS`. */
export function EmployeeConcurrentStatusBadge({ row, className }: EmployeeConcurrentStatusBadgeProps) {
  return (
    <Badge variant="outline" className={cn('border-transparent', TONE_CLASS[concurrentStatusTone(row.status)], className)}>
      {concurrentStatusLabel(row)}
    </Badge>
  )
}
