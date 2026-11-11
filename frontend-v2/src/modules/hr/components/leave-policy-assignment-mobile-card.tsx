import type { ReactNode } from 'react'

import type { LeavePolicyAssignment } from '../types/leave-policy'
import { formatPolicyRange } from '../utils/leave-policy-display'
import { LeavePolicyAssignmentStateBadge } from './leave-policy-assignment-state-badge'
import { LeavePolicyCurrentYearQuotas } from './leave-policy-current-year-quotas'

interface LeavePolicyAssignmentMobileCardProps {
  assignment: LeavePolicyAssignment
  /** Nút Kết thúc · Xóa — chỉ truyền khi có quyền ghi. */
  actions?: ReactNode
  /**
   * Bày dòng tên chính sách không. Tắt ở tab Đang phân bổ của CHI TIẾT MỘT CHÍNH SÁCH (duoc-CR-721): cả
   * danh sách là của đúng chính sách đó, tên đã nằm trên tiêu đề trang — cùng lý do `showRoom` của
   * `RoomBookingCard`.
   */
  showPolicy?: boolean
}

/**
 * Thẻ một phân bổ ở khổ điện thoại (duoc-CR-717). Bảng 7 cột trên máy 390px chỉ thấy hai cột đầu, còn cột
 * Thao tác nằm sau một lần cuộn ngang — thẻ xếp dọc đủ người · chính sách · khoảng ngày · trạng thái · nút.
 */
export function LeavePolicyAssignmentMobileCard({
  assignment: a,
  actions,
  showPolicy = true,
}: LeavePolicyAssignmentMobileCardProps) {
  return (
    <div className="space-y-1.5 text-sm">
      <div className="flex items-start justify-between gap-2">
        <span className="min-w-0">
          <span className="font-medium">{a.employee_name || `#${a.employee_id}`}</span>
          {a.employee_code && <span className="text-muted-foreground"> · {a.employee_code}</span>}
        </span>
        <LeavePolicyAssignmentStateBadge state={a.state} />
      </div>
      {showPolicy && <p>{a.policy_name || `#${a.policy_id}`}</p>}
      <p className="text-muted-foreground tabular-nums">
        {formatPolicyRange(a.effective_from, a.effective_to)}
      </p>
      <LeavePolicyCurrentYearQuotas quotas={a.current_year_quotas} />
      {a.note && <p className="text-muted-foreground">{a.note}</p>}
      {actions && <div className="flex gap-1 pt-1">{actions}</div>}
    </div>
  )
}
