import { TONE_CLASS } from '@/shared/ui/status-tone'
import { cn } from '@/shared/utils/cn'
import { employeeStatusLabel } from '../types/employee'

/**
 * Tông màu theo tình trạng làm việc — học cách ERPNext tô nhãn trạng thái cạnh
 * tên nhân sự (`employee_list.js`: Active xanh lá · Suspended cam · Left xám).
 * Mã lạ rơi về xám chứ không đoán.
 */
const STATUS_TONE: Record<string, keyof typeof TONE_CLASS> = {
  official: 'done',
  collaborator: 'progress',
  maternity_leave: 'pending',
  resigned: 'neutral',
}

interface EmployeeStatusIndicatorProps {
  /** Mã tình trạng (`official` · `collaborator` · `maternity_leave` · `resigned`). */
  status: string
  /** Nhãn backend gửi kèm; rỗng thì tự tra bảng mã. */
  statusLabel?: string
  /** `false` = hồ sơ đã ngừng dùng — hiện thêm nhãn đỏ, vì tài khoản đi kèm đã bị khóa. */
  isActive: boolean
  className?: string
}

/** Nhãn tình trạng dạng "chấm + chữ" đặt cạnh tiêu đề hồ sơ (duoc-CR-708). */
export function EmployeeStatusIndicator({
  status,
  statusLabel,
  isActive,
  className,
}: EmployeeStatusIndicatorProps) {
  const label = statusLabel || employeeStatusLabel(status) || status
  return (
    <span className={cn('inline-flex flex-wrap items-center gap-1.5', className)}>
      {label && (
        <span
          className={cn(
            'inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium',
            TONE_CLASS[STATUS_TONE[status] ?? 'neutral'],
          )}
        >
          <span aria-hidden className="size-1.5 rounded-full bg-current" />
          {label}
        </span>
      )}
      {!isActive && (
        <span
          className={cn(
            'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
            TONE_CLASS.danger,
          )}
        >
          Ngừng dùng
        </span>
      )}
    </span>
  )
}
