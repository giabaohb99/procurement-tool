import { INSTANCE_STATUS, TASK_STATUS } from '@/modules/approval/types/approval'
import type { ApprovalInstance } from '@/modules/approval/types/approval'

/**
 * Người đang xem có được bày nút «Rút về để sửa» không — cùng ba điều kiện
 * backend kiểm ở `approval.action_service.withdraw`:
 * - phiên duyệt còn đang chạy (hoặc đang KẸT vì không tìm được người duyệt);
 * - người xem CHÍNH LÀ người trình (so theo mã nhân sự, 0 = chưa gắn hồ sơ →
 *   không ai khớp, kể cả người trình cũng chưa gắn hồ sơ);
 * - chưa có ai duyệt — đã có chữ ký thì phải nhờ Trả lại / Từ chối.
 * Backend vẫn là chốt thật; hàm này chỉ để khỏi bày nút cho người bấm vào sẽ lỗi.
 */
export function canWithdrawApproval(
  instance: ApprovalInstance | null | undefined,
  employeeId: number | null | undefined,
): boolean {
  //  KẸT (không tìm được người duyệt) cũng rút được — backend nhận cả hai, và đó
  //  lại đúng lúc người trình cần rút nhất (code-review 29/09/2026, M1).
  if (
    !instance ||
    (instance.status !== INSTANCE_STATUS.running && instance.status !== INSTANCE_STATUS.blocked)
  )
    return false
  if (!employeeId || instance.started_by_employee_id !== employeeId) return false
  return !(instance.tasks ?? []).some((task) => task.status === TASK_STATUS.approved)
}
