import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import type { PolicyCurrentYearQuota } from '../types/leave-policy'
import { formatCompDays } from '../utils/format-comp-days'

interface LeavePolicyCurrentYearQuotasProps {
  /** `undefined` = backend cũ chưa trả trường này — không vẽ gì thay vì báo "không chạm năm nay" sai. */
  quotas: readonly PolicyCurrentYearQuota[] | undefined
}

/**
 * Ô "Hạn mức năm nay" của một phân bổ (duoc-CR-745) — kiểu mục *Leaves* của ERPNext: mỗi loại nghỉ trong gói một
 * dòng *Phép năm 15 ngày*, bấm vào mở đúng dòng Quỹ phép năm của người đó. Số là hạn mức ĐANG CẤP (có thể đã trộn hai
 * gói nếu đổi giữa năm), không phải số khai trong gói. Phân bổ không chạm năm nay thì gạch ngang; loại chưa có dòng
 * quỹ ghi *chưa cấp quỹ*.
 */
export function LeavePolicyCurrentYearQuotas({ quotas }: LeavePolicyCurrentYearQuotasProps) {
  if (quotas === undefined) return null
  if (quotas.length === 0) return <span className="text-muted-foreground">—</span>
  return (
    <ul className="space-y-0.5" onClick={(e) => e.stopPropagation()}>
      {quotas.map((q) => (
        <li key={q.leave_type_id} className="truncate">
          {q.balance_id > 0 && q.allocated_days !== null ? (
            <Link
              to={appRoutes.hr.leaveBalanceDetail(q.balance_id)}
              className="text-primary underline-offset-2 hover:underline"
              title="Mở dòng Quỹ phép năm"
            >
              {q.leave_type_name} <span className="tabular-nums">{formatCompDays(q.allocated_days)}</span> ngày
            </Link>
          ) : (
            <span className="text-muted-foreground">{q.leave_type_name}: chưa cấp quỹ</span>
          )}
        </li>
      ))}
    </ul>
  )
}
