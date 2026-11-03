import { CalendarX2, Trash2 } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import type { LeavePolicyAssignment } from '../types/leave-policy'

interface LeavePolicyAssignmentRowActionsProps {
  assignment: LeavePolicyAssignment
  /** `employee_id` của người đang đăng nhập — 0 / vắng = tài khoản không gắn hồ sơ. */
  myEmployeeId: number | undefined
  onEnd: (assignment: LeavePolicyAssignment) => void
  onDelete: (assignment: LeavePolicyAssignment) => void
}

/**
 * Nút Kết thúc · Xóa của MỘT phân bổ (duoc-CR-717) — dùng chung cho ô cuối bảng và thẻ khổ điện thoại.
 *
 * ⚠️ Dòng của CHÍNH người đang đăng nhập: không dựng nút, chỉ một dòng chữ. Backend chặn tự sửa / xóa phân
 * bổ của mình (403, D5 — trừ quản trị hệ thống). Giao diện không biết ai là quản trị nếu không nạp danh mục
 * vai trò, nên khóa THỪA cả với quản trị: khóa thừa thì chỉ phải nhờ người khác, mở thừa thì bấm xong mới
 * ăn 403 (cùng luật `holdsSystemAdminRole`).
 */
export function LeavePolicyAssignmentRowActions({
  assignment,
  myEmployeeId,
  onEnd,
  onDelete,
}: LeavePolicyAssignmentRowActionsProps) {
  if (myEmployeeId && assignment.employee_id === myEmployeeId) {
    return <span className="px-2 text-xs text-muted-foreground">Của bạn — nhờ người khác sửa</span>
  }
  return (
    <>
      <Button type="button" variant="ghost" size="sm" onClick={() => onEnd(assignment)}>
        <CalendarX2 className="size-4" />
        Kết thúc
      </Button>
      <Button type="button" variant="ghost" size="sm" className="text-destructive" onClick={() => onDelete(assignment)}>
        <Trash2 className="size-4" />
        Xóa
      </Button>
    </>
  )
}
