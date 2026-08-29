import type { LucideIcon } from 'lucide-react'

import { IconTooltip } from '@/shared/ui/icon-tooltip'
import { cn } from '@/shared/utils/cn'

interface TaskDetailRowProps {
  icon: LucideIcon
  /**
   * Tên trường. Bỏ trống với những hàng mà biểu tượng đã nói hết nghĩa (người
   * phụ trách, thời gian, mô tả) — đúng cách Lark vẽ panel: bớt một cột chữ thì
   * giá trị nhích sát lề trái và cả panel đọc nhanh hơn hẳn.
   */
  label?: string
  /** Chữ đọc cho trình đọc màn hình khi hàng KHÔNG có nhãn nhìn thấy. */
  srLabel?: string
  children: React.ReactNode
  className?: string
}

/**
 * Một hàng thuộc tính trong panel chi tiết: `biểu tượng · [tên trường] · giá trị`.
 *
 * Trước đây mỗi hàng là lưới `7rem 1fr` toàn chữ, giá trị lại là ô chọn rộng
 * 11rem — panel nhìn như một biểu mẫu nhập liệu chứ không phải bảng thuộc tính.
 * Hàng ở đây gọn theo chiều dọc (`py-1`) và để giá trị tự co, nên chip hiện
 * đúng bằng bề rộng nội dung như trên thẻ kanban.
 */
export function TaskDetailRow({
  icon: Icon,
  label,
  srLabel,
  children,
  className,
}: TaskDetailRowProps) {
  return (
    <div className={cn('flex items-start gap-2.5 py-1', className)}>
      {/*  Biểu tượng nào cũng có tooltip: hàng bỏ nhãn chữ (người phụ trách,
           thời gian, mô tả) thì đây là chỗ DUY NHẤT đọc ra hàng đó là gì. */}
      <IconTooltip label={label ?? srLabel ?? ''} side="left">
        <span className="flex h-7 w-5 shrink-0 cursor-default items-center justify-center text-muted-foreground">
          <Icon className="size-4" aria-hidden />
        </span>
      </IconTooltip>
      {label ? (
        <span className="flex h-7 w-28 shrink-0 items-center truncate text-sm text-muted-foreground">
          {label}
        </span>
      ) : (
        srLabel && <span className="sr-only">{srLabel}</span>
      )}
      <div className="flex min-w-0 flex-1 flex-wrap items-center gap-1.5">{children}</div>
    </div>
  )
}

/**
 * Ô giá trị RỖNG — chữ mờ kiểu «Thêm mô tả» của Lark, bấm được.
 *
 * Không dùng `<Input placeholder>` cho những chỗ này: một hàng ô nhập viền xám
 * chồng lên nhau làm panel nặng, trong khi phần lớn thời gian người ta chỉ ĐỌC.
 */
export function EmptyValueButton({
  children,
  onClick,
  disabled,
}: {
  children: React.ReactNode
  onClick: () => void
  disabled?: boolean
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={cn(
        'rounded-md px-1.5 py-1 text-left text-sm text-muted-foreground',
        !disabled && 'hover:bg-accent hover:text-foreground',
        disabled && 'cursor-default',
      )}
    >
      {children}
    </button>
  )
}
