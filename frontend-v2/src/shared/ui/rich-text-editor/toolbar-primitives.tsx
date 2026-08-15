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

interface ToolbarButtonProps {
  icon: LucideIcon
  label: string
  /** Đang bật (chữ đậm, canh giữa…) — tô nền cho thấy trạng thái. */
  active?: boolean
  disabled?: boolean
  onClick: () => void
}

export function ToolbarButton({
  icon: Icon,
  label,
  active,
  disabled,
  onClick,
}: ToolbarButtonProps) {
  return (
    <Button
      type="button"
      variant="ghost"
      size="icon-sm"
      title={label}
      aria-label={label}
      aria-pressed={active}
      disabled={disabled}
      // Giữ con trỏ trong vùng soạn thảo: mất focus là mất luôn đoạn đang chọn
      // nên lệnh sẽ áp vào chỗ khác.
      onMouseDown={(event) => event.preventDefault()}
      onClick={onClick}
      className={cn(active && 'bg-accent text-accent-foreground')}
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

interface ColorSwatchesProps {
  colors: string[]
  onPick: (color: string) => void
  onClear: () => void
  clearLabel: string
}

/** Lưới ô màu + một dòng "bỏ màu". */
export function ColorSwatches({ colors, onPick, onClear, clearLabel }: ColorSwatchesProps) {
  return (
    <div className="p-1">
      <div className="grid grid-cols-5 gap-1">
        {colors.map((color) => (
          <button
            key={color}
            type="button"
            title={color}
            aria-label={color}
            onMouseDown={(event) => event.preventDefault()}
            onClick={() => onPick(color)}
            className="size-6 rounded border border-border/60 transition-transform hover:scale-110"
            style={{ backgroundColor: color }}
          />
        ))}
      </div>
      <button
        type="button"
        onMouseDown={(event) => event.preventDefault()}
        onClick={onClear}
        className="mt-1 w-full rounded px-2 py-1 text-left text-xs text-muted-foreground hover:bg-accent"
      >
        {clearLabel}
      </button>
    </div>
  )
}
