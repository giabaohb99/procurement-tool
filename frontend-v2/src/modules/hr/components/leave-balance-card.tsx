import { ChevronRight } from 'lucide-react'

import { cn } from '@/shared/utils/cn'
import type { LeaveBalance } from '../types/leave'
import { hasQuota } from '../utils/leave-balance-quota'

interface LeaveBalanceCardProps {
  balance: LeaveBalance
}

/**
 * Một dòng QUỸ PHÉP ở khổ màn hẹp — xem `DataTableProps.mobileCard`.
 *
 * ⚠️ **Bảng quỹ có ELEVEN cột, mười trong đó là số.** Trên máy 393px người dùng
 * chỉ thấy hai cột đầu (*Nhân sự* · *Loại nghỉ*) — tức là đúng phần KHÔNG có
 * con số nào, còn «Còn lại» — thứ duy nhất người ta mở màn này để xem — nằm sau
 * một thao tác cuộn ngang qua chín cột. Thẻ đảo lại thứ bậc đó: **số CÒN LẠI to
 * nhất, nằm bên phải**, tên người bên trái, mấy con số phụ gom thành một dòng
 * chú thích.
 *
 * ⚠️ **Chỉ bày ô KHÁC 0.** Thâm niên · chuyển năm trước · điều chỉnh tay hầu như
 * luôn bằng 0; in hết ra thì thẻ nào cũng bốn dòng số giống hệt nhau và người
 * đọc không nhặt ra được thẻ nào có gì đặc biệt. Cùng lý do bảng vẽ số 0 thành
 * dấu gạch mờ. Riêng «Còn lại» thì luôn hiện — ở đó số 0 nghĩa là **hết phép**,
 * đúng thứ phải đập vào mắt.
 */
export function LeaveBalanceCard({ balance }: LeaveBalanceCardProps) {
  const extras: string[] = []
  if (balance.seniority_days) extras.push(`+${balance.seniority_days} thâm niên`)
  if (balance.carried_days) extras.push(`+${balance.carried_days} chuyển năm trước`)
  if (balance.carried_out_days) extras.push(`${balance.carried_out_days} đã chuyển đi`)
  if (balance.carried_expired_days) extras.push(`${balance.carried_expired_days} hết hạn`)
  if (balance.adjusted_days) {
    const sign = balance.adjusted_days > 0 ? '+' : ''
    extras.push(`${sign}${balance.adjusted_days} điều chỉnh tay`)
  }

  return (
    <div className="flex items-start gap-3">
      <div className="min-w-0 flex-1 space-y-1.5">
        <span className="block truncate font-medium text-foreground">
          {balance.employee_name || `#${balance.employee_id}`}
        </span>

        {/*  Loại nghỉ có KHUNG: nó nằm giữa tên người và một dòng chữ số cùng cỡ,
             để trần thì ba dòng đọc thành một đoạn văn không phân vai. */}
        <span className="inline-block rounded border px-1.5 py-0.5 text-xs text-foreground">
          {balance.leave_type_name || `#${balance.leave_type_id}`}
        </span>

        {/*  ⚠️ Cả dòng này ẨN khi mọi số đều 0 — «Hạn mức 0 · Đã nghỉ 0» không
             nói thêm được gì mà con số lớn bên phải chưa nói. Một người có tám
             dòng quỹ thì sáu dòng như vậy (Nghỉ tang chế, Nghỉ bù, Nghỉ cưới
             hỏi…), giữ lại là sáu thẻ chữ giống hệt nhau. */}
        {(balance.allocated_days > 0 || balance.used_days > 0 || balance.pending_days > 0) && (
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
            <span>
              Hạn mức{' '}
              <span className="font-medium text-foreground">{balance.allocated_days}</span>
            </span>
            <span>
              Đã nghỉ <span className="font-medium text-foreground">{balance.used_days}</span>
            </span>
            {balance.pending_days > 0 && (
              //  Hổ phách vì đây là ngày ĐANG GIỮ CHỖ: chưa nghỉ nhưng cũng
              //  không tiêu được nữa — cùng màu với cột tương ứng ở bảng.
              <span className="text-amber-600 dark:text-amber-400">
                Chờ duyệt <span className="font-medium">{balance.pending_days}</span>
              </span>
            )}
          </div>
        )}

        {extras.length > 0 && (
          <p className="text-xs text-muted-foreground">{extras.join(' · ')}</p>
        )}
      </div>

      <div className="flex shrink-0 items-center gap-1">
        <div className="text-right">
          <div
            className={cn(
              'text-lg leading-tight font-semibold tabular-nums',
              //  Số 0 chỉ ĐỎ khi có quỹ mà tiêu hết; loại nghỉ không cấp hạn mức
              //  thì để mờ — xem `hasQuota`.
              balance.remaining_days > 0
                ? 'text-foreground'
                : hasQuota(balance)
                  ? 'text-destructive'
                  : 'text-muted-foreground',
            )}
          >
            {balance.remaining_days}
          </div>
          <div className="text-[11px] text-muted-foreground">còn lại</div>
        </div>

        {/*  Mũi tên nói THẺ NÀY BẤM ĐƯỢC. Màn cảm ứng không có con trỏ đổi hình
             khi rê qua, nên phải nói bằng hình. */}
        <ChevronRight className="size-4 text-muted-foreground" aria-hidden="true" />
      </div>
    </div>
  )
}
