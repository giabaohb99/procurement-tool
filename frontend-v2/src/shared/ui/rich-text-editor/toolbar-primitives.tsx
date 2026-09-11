import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'

import { Button } from '@/shared/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { cn } from '@/shared/utils/cn'

/**
 * Mấy mẩu dùng chung của thanh công cụ soạn thảo.
 *
 * Nút bấm ở đây đều `type="button"`: thanh công cụ hay nằm trong thẻ `<form>`,
 * để mặc định thì bấm "In đậm" là trình duyệt gửi luôn cả form.
 */

/**
 * ⚠️ **Kế thừa hết prop của `Button` và SPREAD chúng xuống — đừng quay lại kiểu
 * liệt kê tay vài prop.**
 *
 * Nút này có lúc làm con của `PopoverTrigger asChild` (`EditorFormatPopover`).
 * Lúc đó Radix nhét vào nút con cả `ref` lẫn `onClick`, `aria-expanded`,
 * `data-state`. Bản cũ chỉ nhận đúng `icon/label/active/disabled/onClick` nên
 * **nuốt sạch số còn lại**, và hậu quả im lặng: mất `ref` nghĩa là Radix không
 * có mốc neo, Floating UI không chạy, tấm popover đứng nguyên ở trạng thái chưa
 * định vị (`transform: translate(0,-200%)`) — tức mở ra **ngoài màn hình phía
 * trên**, không lỗi, không cảnh báo, chỉ là bấm mà chẳng thấy gì.
 */
interface ToolbarButtonProps extends React.ComponentProps<typeof Button> {
  icon: LucideIcon
  label: string
  /** Đang bật (chữ đậm, canh giữa…) — tô nền cho thấy trạng thái. */
  active?: boolean
}

export function ToolbarButton({
  icon: Icon,
  label,
  active,
  className,
  ...rest
}: ToolbarButtonProps) {
  return (
    <Button
      type="button"
      variant="ghost"
      size="icon-sm"
      title={label}
      aria-label={label}
      aria-pressed={active}
      // Giữ con trỏ trong vùng soạn thảo: mất focus là mất luôn đoạn đang chọn
      // nên lệnh sẽ áp vào chỗ khác.
      onMouseDown={(event) => event.preventDefault()}
      className={cn(active && 'bg-accent text-accent-foreground', className)}
      {...rest}
    >
      <Icon className="size-4" />
    </Button>
  )
}

/** Vạch ngăn giữa các nhóm lệnh. */
export function ToolbarDivider() {
  return <span aria-hidden className="mx-0.5 h-5 w-px shrink-0 bg-border" />
}

interface ToolbarSelectProps {
  value: string
  onValueChange: (value: string) => void
  options: { label: string; value: string }[]
  label: string
  className?: string
  /** Ghi font vào chính ô select để nhìn được mặt chữ trước khi chọn. */
  previewFont?: boolean
}

export function ToolbarSelect({
  value,
  onValueChange,
  options,
  label,
  className,
  previewFont,
}: ToolbarSelectProps) {
  return (
    <Select value={value} onValueChange={onValueChange}>
      <SelectTrigger size="sm" aria-label={label} title={label} className={className}>
        <SelectValue placeholder={label} />
      </SelectTrigger>
      <SelectContent>
        {options.map((option) => (
          <SelectItem
            key={option.value}
            value={option.value}
            style={previewFont ? { fontFamily: option.value } : undefined}
          >
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

interface ToolbarMenuProps {
  icon: LucideIcon
  label: string
  children: ReactNode
}

/** Nút mở bảng chọn nhỏ (màu chữ, chèn bảng…). */
export function ToolbarMenu({ icon: Icon, label, children }: ToolbarMenuProps) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          type="button"
          variant="ghost"
          size="icon-sm"
          title={label}
          aria-label={label}
          onMouseDown={(event) => event.preventDefault()}
        >
          <Icon className="size-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-auto">
        {children}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

