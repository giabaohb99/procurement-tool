import { Badge } from '@/shared/ui/badge'
import {
  CHANGE_REQUEST_STATUS,
  getChangeRequestStatusLabel,
} from '../utils/employee-change-request-status'

/**
 * Sắc thái theo cùng luật với `LeaveStatusBadge`: chờ = hổ phách, xong tốt = xanh lá, từ chối =
 * đỏ, rút lại = xám trung tính (thang `zinc`, không `slate` — `slate` ám xanh, lẫn với navy).
 */
const TONES: Record<number, string> = {
  [CHANGE_REQUEST_STATUS.PENDING]:
    'border-amber-300 bg-amber-100 text-amber-800 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-200',
  [CHANGE_REQUEST_STATUS.APPROVED]:
    'border-emerald-300 bg-emerald-100 text-emerald-800 dark:border-emerald-700 dark:bg-emerald-950 dark:text-emerald-200',
  [CHANGE_REQUEST_STATUS.REJECTED]:
    'border-destructive/40 bg-destructive/15 text-destructive dark:bg-destructive/25',
  [CHANGE_REQUEST_STATUS.WITHDRAWN]:
    'border-zinc-400 bg-zinc-200 text-zinc-700 dark:border-zinc-500 dark:bg-zinc-700 dark:text-zinc-200',
}

export function EmployeeChangeRequestStatusBadge({ status }: { status: number }) {
  return (
    <Badge variant="outline" className={TONES[status] ?? TONES[CHANGE_REQUEST_STATUS.WITHDRAWN]}>
      {getChangeRequestStatusLabel(status)}
    </Badge>
  )
}
