import { Badge } from '@/shared/ui/badge'
import { TONE_CLASS } from '@/shared/ui/status-tone'
import { cn } from '@/shared/utils/cn'
import {
  LEAVE_POLICY_ASSIGNMENT_STATE,
  LEAVE_POLICY_ASSIGNMENT_STATE_LABELS,
  type LeavePolicyAssignmentState,
} from '../types/leave-policy'

/** Sắp tới = xanh dương (chờ tới ngày) · Đang hiệu lực = xanh lá · Đã kết thúc = xám. */
const STATE_TONE: Record<LeavePolicyAssignmentState, string> = {
  [LEAVE_POLICY_ASSIGNMENT_STATE.UPCOMING]: TONE_CLASS.progress,
  [LEAVE_POLICY_ASSIGNMENT_STATE.ACTIVE]: TONE_CLASS.done,
  [LEAVE_POLICY_ASSIGNMENT_STATE.ENDED]: TONE_CLASS.neutral,
}

/**
 * Huy hiệu trạng thái phân bổ chính sách (duoc-CR-717). Đọc thẳng `state` của backend — KHÔNG tự so
 * ngày ở máy khách: đồng hồ máy có thể lệch ngày Việt Nam, và hai nơi tính là hai câu trả lời.
 */
export function LeavePolicyAssignmentStateBadge({ state }: { state: LeavePolicyAssignmentState }) {
  return (
    <Badge variant="outline" className={cn('border-transparent', STATE_TONE[state] ?? TONE_CLASS.neutral)}>
      {LEAVE_POLICY_ASSIGNMENT_STATE_LABELS[state] ?? `#${state}`}
    </Badge>
  )
}
