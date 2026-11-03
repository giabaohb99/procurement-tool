import type { ReactNode } from 'react'

import type { LeavePolicyAssignment } from '../types/leave-policy'
import { formatPolicyRange } from '../utils/leave-policy-display'
import { LeavePolicyAssignmentStateBadge } from './leave-policy-assignment-state-badge'

interface LeavePolicyAssignmentMobileCardProps {
  assignment: LeavePolicyAssignment
  /** Nút Kết thúc · Xóa — chỉ truyền khi có quyền ghi. */
  actions?: ReactNode
}

/**
 * Thẻ một phân bổ ở khổ điện thoại (duoc-CR-717). Bảng 7 cột trên máy 390px chỉ thấy hai cột đầu, còn cột
 * Thao tác nằm sau một lần cuộn ngang — thẻ xếp dọc đủ người · chính sách · khoảng ngày · trạng thái · nút.
 */
export function LeavePolicyAssignmentMobileCard({ assignment: a, actions }: LeavePolicyAssignmentMobileCardProps) {
  return (
    <div className="space-y-1.5 px-3 py-2.5 text-sm">
      <div className="flex items-start justify-between gap-2">
        <span className="min-w-0">
          <span className="font-medium">{a.employee_name || `#${a.employee_id}`}</span>
          {a.employee_code && <span className="text-muted-foreground"> · {a.employee_code}</span>}
        </span>
        <LeavePolicyAssignmentStateBadge state={a.state} />
      </div>
      <p>{a.policy_name || `#${a.policy_id}`}</p>
      <p className="text-muted-foreground tabular-nums">{formatPolicyRange(a.effective_from, a.effective_to)}</p>
      {a.note && <p className="text-muted-foreground">{a.note}</p>}
      {actions && <div className="flex gap-1 pt-1">{actions}</div>}
    </div>
  )
}
