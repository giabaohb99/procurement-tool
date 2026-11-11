import { ArrowRight } from 'lucide-react'

import { cn } from '@/shared/utils/cn'
import type { PolicyQuotaChange } from '../types/leave-policy'
import { formatCompDays } from '../utils/format-comp-days'
import type { LeaveTypeNameLookup } from '../utils/leave-policy-display'

interface LeavePolicyBalanceChangesProps {
  changes: readonly PolicyQuotaChange[]
  typeName: LeaveTypeNameLookup
  className?: string
}

/**
 * Bảng nhỏ "Loại nghỉ · Hiện tại → Sau phân bổ" của quỹ NĂM NAY (duoc-CR-717) — dùng chung cho hộp
 * phân bổ một người và khung kết quả hàng loạt. "Hiện tại" = số đang cấp, hoặc số SẼ cấp nếu người đó
 * chưa có dòng quỹ loại đó. Loại không đổi vẫn hiện (mờ) để người xem thấy gói có chạm tới loại đó.
 */
export function LeavePolicyBalanceChanges({ changes, typeName, className }: LeavePolicyBalanceChangesProps) {
  if (changes.length === 0) {
    return (
      <p className={cn('text-sm text-muted-foreground', className)}>
        Quỹ năm nay không đổi hạn mức loại nghỉ nào. Thường vì số ngày của chính sách bằng đúng hạn mức đang cấp, chính
        sách chỉ khai loại nghỉ không trừ quỹ (ốm đau, cưới hỏi, tang chế…), hoặc khoảng ngày không chạm năm nay.
      </p>
    )
  }
  return (
    <div className={cn('rounded-md border', className)}>
      <div className="grid grid-cols-[1fr_auto] gap-3 border-b bg-muted px-3 py-1.5 text-xs font-medium text-muted-foreground">
        <span>Loại nghỉ</span>
        <span>Hiện tại → Sau phân bổ</span>
      </div>
      <ul className="divide-y">
        {changes.map((change) => {
          const same = change.before === change.after
          return (
            <li
              key={change.leave_type_id}
              className={cn('grid grid-cols-[1fr_auto] items-center gap-3 px-3 py-1.5 text-sm', same && 'text-muted-foreground')}
            >
              <span className="min-w-0 truncate">{typeName(change.leave_type_id)}</span>
              <span className="flex items-center gap-1.5 tabular-nums">
                {formatCompDays(change.before)}
                <ArrowRight className="size-3.5" aria-label="thành" />
                <span className={cn(!same && 'font-semibold text-primary')}>{formatCompDays(change.after)}</span>
                <span className="text-xs text-muted-foreground">ngày</span>
              </span>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
