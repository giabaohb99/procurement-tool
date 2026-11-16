import { ChevronRight } from 'lucide-react'

import { cn } from '@/shared/utils/cn'
import type { LeaveBalanceRow } from '../utils/group-leave-balances'
import { pickAccrualInfo } from '../utils/leave-accrual-status'
import { LeaveAccrualStatusBadge } from './leave-accrual-status-badge'
import { LeaveBalanceCard } from './leave-balance-card'

interface LeaveBalanceRowCardProps {
  row: LeaveBalanceRow
  expanded: boolean
  /** Ẩn nhãn *Chưa có HĐLĐ* (duoc-CR-762 phương án B). */
  hideNoContract?: boolean
}

/**
 * Một HÀNG của bảng Quỹ phép ở khổ màn hẹp (xem `DataTableProps.mobileCard`).
 *
 * Chỉ phân vai ba dạng hàng rồi giao việc: hàng có dòng quỹ thật thì vẫn là
 * `LeaveBalanceCard` cũ, hàng NHÓM mới cần thẻ riêng vì nó không có dòng quỹ nào
 * để mà bày — nó là một phép cộng.
 */
export function LeaveBalanceRowCard({ row, expanded, hideNoContract = false }: LeaveBalanceRowCardProps) {
  if (row.kind === 'group') {
    const { group } = row
    return (
      <div className="flex items-start gap-3">
        <ChevronRight
          className={cn(
            'mt-0.5 size-4 shrink-0 text-muted-foreground transition-transform',
            expanded && 'rotate-90',
          )}
        />
        <div className="min-w-0 flex-1 space-y-1">
          <div className="flex min-w-0 items-center gap-1.5">
            <span className="truncate font-medium text-foreground">{group.employeeName}</span>
            <LeaveAccrualStatusBadge
              info={pickAccrualInfo(group.balances, hideNoContract)}
              hideContractWarning={hideNoContract}
            />
          </div>
          <p className="text-xs text-muted-foreground">
            {group.balances.length} loại nghỉ · tổng cấp{' '}
            <span className="font-medium text-foreground">{group.totals.total_days}</span> · đã
            nghỉ <span className="font-medium text-foreground">{group.totals.used_days}</span>
          </p>
        </div>
        <div className="shrink-0 text-right">
          <span
            className={cn(
              'block text-xl leading-none font-semibold tabular-nums',
              group.totals.remaining_days > 0
                ? 'text-foreground'
                : group.hasQuota
                  ? 'text-destructive'
                  : 'text-muted-foreground',
            )}
          >
            {group.totals.remaining_days}
          </span>
          <span className="text-xs text-muted-foreground">còn lại</span>
        </div>
      </div>
    )
  }

  //  Dòng con thụt vào để đọc ra là nó thuộc thẻ ngay phía trên — ở khổ hẹp
  //  không có đường kẻ cột nào nói hộ điều đó.
  return (
    <div className={cn(row.kind === 'child' && 'border-l-2 border-border pl-3')}>
      <LeaveBalanceCard
        balance={row.balance}
        hideEmployeeName={row.kind === 'child'}
        hideNoContract={hideNoContract}
      />
    </div>
  )
}
