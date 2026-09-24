import { ChevronRight } from 'lucide-react'

import { cn } from '@/shared/utils/cn'
import type { LeaveBalanceRow } from '../utils/group-leave-balances'

/**
 * Ô ĐỊNH DANH — chỗ duy nhất phân biệt ba dạng hàng.
 *
 * ⚠️ Người chỉ có MỘT loại nghỉ không có mũi tên: tên và loại nghỉ nằm cùng
 * dòng, `«Đoàn Minh Khôi · Phép năm»`. Cho họ một mũi tên bung ra đúng một dòng
 * chép lại con số vừa đọc là bắt bấm thêm một nhịp để nhận lại không gì cả — mà
 * công ty mới khai mỗi «Phép năm» thì đó là TOÀN BỘ 261 hàng.
 */
export function NameCell({
  row,
  expanded,
  onToggle,
}: {
  row: LeaveBalanceRow
  expanded: ReadonlySet<number>
  onToggle: (employeeId: number) => void
}) {
  if (row.kind === 'child') {
    return (
      //  Thụt lề bằng đúng bề rộng ô mũi tên của hàng cha, để tên loại nghỉ
      //  thẳng hàng với tên người phía trên nó.
      <span className="flex items-center gap-2 pl-7 text-muted-foreground">
        <span className="truncate">{row.balance.leave_type_name || `#${row.balance.leave_type_id}`}</span>
      </span>
    )
  }

  if (row.kind === 'single') {
    return (
      <span className="flex items-center gap-2 pl-7">
        <span className="truncate font-medium">{row.group.employeeName}</span>
        <span className="shrink-0 text-xs text-muted-foreground">
          · {row.balance.leave_type_name || `#${row.balance.leave_type_id}`}
        </span>
      </span>
    )
  }

  const isOpen = expanded.has(row.group.employeeId)
  return (
    <span className="flex items-center gap-1">
      <button
        type="button"
        //  ⚠️ `stopPropagation`: cả hàng cũng bắt click để bung/thu, không chặn
        //  thì bấm đúng mũi tên là chạy hai lần và nhóm đóng lại ngay lập tức.
        onClick={(event) => {
          event.stopPropagation()
          onToggle(row.group.employeeId)
        }}
        aria-expanded={isOpen}
        aria-label={`${isOpen ? 'Thu gọn' : 'Bung'} quỹ phép của ${row.group.employeeName}`}
        className="shrink-0 rounded p-1 text-muted-foreground hover:bg-accent hover:text-foreground"
      >
        <ChevronRight className={cn('size-4 transition-transform', isOpen && 'rotate-90')} />
      </button>
      <span className="truncate font-medium">{row.group.employeeName}</span>
      <span className="shrink-0 text-xs text-muted-foreground">
        · {row.group.balances.length} loại nghỉ
      </span>
    </span>
  )
}

/**
 * Một ô SỐ NGÀY trong bảng quỹ.
 *
 * ⚠️ Số `0` hiện thành dấu gạch mờ, không phải chữ "0". Bảng này có bảy cột số
 * mà bốn cột trong đó hầu như luôn bằng 0 (thâm niên, chuyển năm, điều chỉnh
 * tay) — in "0" và "+0" ra hết thì cả bảng đặc số, và mắt không còn nhặt ra
 * được ô nào thật sự có giá trị. Cột «Còn lại» thì `alwaysShow`: ở đó số 0 mang
 * nghĩa **hết phép**, đúng thứ phải đập vào mắt.
 */
export function DayCount({
  value,
  signed = false,
  alwaysShow = false,
  className,
}: {
  value: number
  /** Thêm dấu `+` khi dương. Số âm tự mang dấu `-`, không ghép tay. */
  signed?: boolean
  alwaysShow?: boolean
  className?: string
}) {
  if (!value && !alwaysShow) {
    return <span className="text-muted-foreground/40">—</span>
  }
  const prefix = signed && value > 0 ? '+' : ''
  return <span className={cn('tabular-nums', className)}>{`${prefix}${value}`}</span>
}
