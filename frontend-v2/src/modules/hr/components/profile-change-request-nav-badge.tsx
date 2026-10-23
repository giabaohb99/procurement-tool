import { usePermission } from '@/core/authorization/use-permission'
import { useChangeRequestPendingCount } from '../hooks/use-employee-change-requests'

/**
 * Huy hiệu trên mục menu «Duyệt sửa hồ sơ» — số đề nghị sửa hồ sơ đang chờ (duoc-CR-676).
 * Không có việc thì không hiện gì (một số 0 nằm trên menu cả ngày dạy người ta lướt qua chỗ đó).
 * Tự tắt query khi thiếu `employee.write` — cửa đếm trả 403.
 */
export function ProfileChangeRequestNavBadge() {
  const { can } = usePermission()
  const { data } = useChangeRequestPendingCount(can('employee', 'write'))
  const count = data?.count ?? 0
  if (count <= 0) return null
  return (
    <span
      //  `ml-auto` do chính huy hiệu mang — cùng lối `DocumentApprovalNavBadge`.
      className="ml-auto rounded-full bg-primary px-1.5 py-0.5 text-[0.6875rem] font-semibold text-primary-foreground"
      aria-label={`${count} đề nghị sửa hồ sơ đang chờ duyệt`}
    >
      {count > 99 ? '99+' : count}
    </span>
  )
}
