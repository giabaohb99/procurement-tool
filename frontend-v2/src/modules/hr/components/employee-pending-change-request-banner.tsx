import { FilePen } from 'lucide-react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { useChangeRequests } from '../hooks/use-employee-change-requests'
import type { Employee } from '../types/employee'
import { CHANGE_REQUEST_STATUS } from '../utils/employee-change-request-status'

interface EmployeePendingChangeRequestBannerProps {
  employee: Employee
  /** Chỉ người duyệt được (`employee.write`) mới hỏi — cửa danh sách trả 403 với người khác. */
  enabled: boolean
}

/**
 * Dải báo "người này đang có đề nghị sửa hồ sơ chờ duyệt" trên màn chi tiết nhân sự (duoc-CR-676).
 *
 * Rẻ: MỘT lời gọi danh sách sẵn có, lọc ĐÚNG `employee_id` + `status = chờ duyệt` (review L1 —
 * bản trước dùng `q = mã NV`, tìm chuỗi con nên NSU001 dính cả NSU0010…NSU0019). Mỗi người tối đa
 * một đề nghị chờ nên một dòng là đủ; vẫn lọc lại `employee_id` ở đây cho chắc.
 */
export function EmployeePendingChangeRequestBanner({
  employee,
  enabled,
}: EmployeePendingChangeRequestBannerProps) {
  const { data } = useChangeRequests(
    { employee_id: employee.id, status: CHANGE_REQUEST_STATUS.PENDING, page: 1, page_size: 1 },
    enabled && employee.id > 0,
  )
  const pending = data?.items.find(
    (item) => item.employee_id === employee.id && item.status === CHANGE_REQUEST_STATUS.PENDING,
  )
  if (!pending) return null

  return (
    <div
      role="status"
      className="mb-4 flex flex-wrap items-center gap-2 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900 dark:border-amber-700 dark:bg-amber-950/40 dark:text-amber-100"
    >
      <FilePen className="size-4 shrink-0" />
      <span>Nhân viên này đang có một đề nghị sửa hồ sơ chờ duyệt.</span>
      <Link
        to={appRoutes.hr.profileChangeRequestDetail(pending.id)}
        className="font-medium underline underline-offset-2"
      >
        Xem đề nghị
      </Link>
    </div>
  )
}
