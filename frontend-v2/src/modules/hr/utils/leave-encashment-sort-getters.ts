import type { LeaveEncashment } from '../types/leave-encashment'
import { approvalLifecycleRank } from './approval-lifecycle-rank'
import type { CellGetters } from '@/shared/utils/sort-rows-by-cell'

/** Vòng đời YCTT theo thứ tự đọc — khớp `_PAYMENT_STATUS_ORDER` ở backend (`comp_encashment_sort_expressions.py`). */
const PAYMENT_STATUS_ORDER = ['draft', 'submitted', 'approved', 'paid', 'cancelled'] as const

/**
 * Giá trị ô đang hiện của từng cột xếp được của Phiếu thanh toán nghỉ phép (duoc-CR-744) — dùng để xếp hàng
 * đợi *Cần tôi duyệt* tại chỗ (endpoint `/to-approve` trả hết, không nhận `sort_by`). Hai phạm vi có phân
 * trang xếp ở server theo cùng các khóa. `reason_kind` là mã số đã theo thứ tự hiển thị; `status` theo hạng dòng đời như máy chủ (duoc-CR-748); trạng
 * thái chi xếp theo HẠNG vòng đời, phiếu chưa có YCTT là ô trống (xuống cuối).
 */
export const ENCASHMENT_SORT_GETTERS: CellGetters<LeaveEncashment> = {
  id: (r) => r.id,
  code: (r) => r.code,
  employee_name: (r) => r.employee_name,
  leave_type_name: (r) => r.leave_type_name,
  balance_year: (r) => r.balance_year,
  reason_kind: (r) => r.reason_kind,
  days: (r) => r.days,
  status: (r) => approvalLifecycleRank(r.status),
  payment_status: (r) => {
    const rank = (PAYMENT_STATUS_ORDER as readonly string[]).indexOf(r.payment_status)
    return rank < 0 ? null : rank
  },
  note: (r) => r.note,
  created_at: (r) => r.created_at,
}
