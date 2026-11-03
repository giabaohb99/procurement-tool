import { ScrollText } from 'lucide-react'
import { Link } from 'react-router-dom'

import { canManageEntity } from '@/app/router/module-visibility'
import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { useLeavePolicyAssignments, useLeavePolicyLines } from '../hooks/use-leave-policy'
import { formatCompDays } from '../utils/format-comp-days'
import { formatPolicyRange } from '../utils/leave-policy-display'
import { todayInVietnamISO } from '../utils/work-roster-range'

interface LeaveBalancePolicyNoteProps {
  employeeId: number
  leaveTypeId: number
  /** Năm của dòng quỹ đang xem — chỉ năm hiện tại (giờ VN) mới dựng dòng này. */
  year: number
}

/**
 * Dòng nhỏ trên chi tiết dòng quỹ (duoc-CR-717): HÔM NAY người này đang theo CHÍNH SÁCH nào, hay theo hạn
 * mức của loại nghỉ. Đọc được dòng của gói (`leave_type.read`) thì nói thêm gói có khai loại nghỉ này không
 * — gói không khai loại đó thì loại đó vẫn theo hạn mức của loại nghỉ (D1a), đây là chỗ hay hiểu nhầm nhất.
 *
 * ⚠️ Chỉ dựng cho dòng quỹ của NĂM HIỆN TẠI (review M1): câu hỏi gửi API là "phân bổ còn hiệu lực hôm nay",
 * nên đặt dưới quỹ năm cũ / năm sau thì nó giải thích nhầm năm. Năm khác → không dựng gì. Lỗi API cũng
 * không dựng gì — nói "không có chính sách nào" khi thật ra là không tải được thì sai sự thật.
 *
 * Gác `leave_balance.read` (khóa của phân bổ); thiếu quyền thì không dựng gì, không gọi API. Liên kết sang
 * gói chỉ hiện khi QUẢN LÝ được loại nghỉ (`canManageEntity('leave_type')`, đúng luật của thẻ Thiết lập —
 * route gói gác quyền quản lý, chỉ có `read` thì bấm vào là 403); còn lại tên gói là chữ thường.
 */
export function LeaveBalancePolicyNote({ employeeId, leaveTypeId, year }: LeaveBalancePolicyNoteProps) {
  const { can } = usePermission()
  const today = todayInVietnamISO()
  const isCurrentYear = year === Number(today.slice(0, 4))
  const canRead = can('leave_balance', 'read') && employeeId > 0 && isCurrentYear
  const { data, isLoading, isError } = useLeavePolicyAssignments(
    { employee_id: employeeId, active_on: today, page_size: 1 },
    { enabled: canRead },
  )
  const active = data?.items[0]
  const { data: lines } = useLeavePolicyLines(active?.policy_id ?? 0, canRead && can('leave_type', 'read'))

  if (!canRead || isLoading || isError || !data) return null

  const line = lines?.items.find((l) => l.leave_type_id === leaveTypeId)
  return (
    <p className="flex items-start gap-2 rounded-md border bg-muted/40 px-3 py-2 text-sm">
      <ScrollText className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
      {active ? (
        <span>
          Chính sách đang áp hôm nay:{' '}
          {canManageEntity('leave_type', can) ? (
            <Link className="font-medium text-primary hover:underline" to={appRoutes.hr.leavePolicyDetail(active.policy_id)}>
              {active.policy_name}
            </Link>
          ) : (
            <strong>{active.policy_name}</strong>
          )}{' '}
          ({formatPolicyRange(active.effective_from, active.effective_to)})
          {lines &&
            (line
              ? ` — khai ${formatCompDays(line.annual_days)} ngày/năm cho loại nghỉ này.`
              : ' — chính sách không khai loại nghỉ này nên vẫn theo hạn mức của loại nghỉ.')}
        </span>
      ) : (
        <span className="text-muted-foreground">
          Hôm nay không có chính sách nghỉ phép nào đang áp — theo hạn mức của loại nghỉ.
        </span>
      )}
    </p>
  )
}
