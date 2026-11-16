import { DialogDescription, DialogTitle } from '@/shared/ui/dialog'
import { cn } from '@/shared/utils/cn'
import { formatShiftDayLabel } from '../utils/work-shift-date'

export type ShiftStatus = 'shift' | 'shift-off' | 'template'

const STATUS: Record<ShiftStatus, { label: string; className: string }> = {
  //  Cùng màu thẻ ca trên lưới — người xem nhận ra ngay đây là ô "ngoại lệ".
  shift: { label: 'Ca xếp riêng', className: 'bg-shift text-shift-foreground' },
  'shift-off': { label: 'Nghỉ (xếp ca)', className: 'bg-warning/15 text-warning' },
  template: { label: 'Theo mẫu tuần', className: 'bg-muted text-muted-foreground' },
}

interface WorkShiftDialogHeaderProps {
  fullName: string
  date: string
  status: ShiftStatus
}

/**
 * Đầu hộp xếp ca, căn TRÁI: dòng 1 tên nhân sự (cắt khi dài), dòng 2 thứ + ngày đầy đủ; bên phải một nhãn trạng thái
 * của ô. Chừa chỗ bên phải cho nút đóng X của khung.
 */
export function WorkShiftDialogHeader({ fullName, date, status }: WorkShiftDialogHeaderProps) {
  const chip = STATUS[status]
  return (
    <div className="flex items-start gap-3 border-b px-5 pt-5 pb-4 pr-12">
      <div className="min-w-0 flex-1 space-y-0.5">
        <DialogTitle className="truncate text-base font-semibold">{fullName}</DialogTitle>
        <DialogDescription className="text-sm text-muted-foreground">{formatShiftDayLabel(date)}</DialogDescription>
      </div>
      <span className={cn('mt-0.5 shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium', chip.className)}>{chip.label}</span>
    </div>
  )
}
