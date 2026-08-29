import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { cn } from '@/shared/utils/cn'
import { chipClass, dotClass } from '../utils/work-colors'

export interface ChipOption {
  value: string
  label: string
  /**
   * Chữ NGẮN dùng cho chip đang hiện; danh sách thả xuống vẫn dùng `label` đủ
   * chữ. «P3» đọc trên panel là đủ, nhưng lúc CHỌN thì phải thấy «P3 — Vừa».
   */
  short?: string
  /** Tên màu trong `WORK_COLORS`; bỏ trống thì mục hiện bằng chữ thường. */
  color?: string
}

interface TaskChipSelectProps {
  value: string
  options: ChipOption[]
  placeholder: string
  disabled?: boolean
  ariaLabel: string
  /** `dot` = chấm màu + chữ (cột kanban), `chip` = viên màu (độ ưu tiên, nhãn). */
  variant?: 'chip' | 'dot'
  onChange: (value: string) => void
}

/**
 * Ô chọn MỘT giá trị, nhưng nhìn như một chip trên thẻ chứ không như ô nhập.
 *
 * Panel cũ đặt `SelectTrigger` rộng 11rem có viền cho Cột và Độ ưu tiên, nên ba
 * hàng liền nhau là ba hộp xám rỗng — trong khi cùng giá trị đó trên thẻ kanban
 * lại là chip màu. Ở đây trigger bỏ viền, co theo chữ và mượn đúng bảng màu của
 * thẻ, nên panel và thẻ nói cùng một ngôn ngữ.
 */
export function TaskChipSelect({
  value,
  options,
  placeholder,
  disabled,
  ariaLabel,
  variant = 'chip',
  onChange,
}: TaskChipSelectProps) {
  const current = options.find((o) => o.value === value)

  return (
    <Select value={value} disabled={disabled} onValueChange={onChange}>
      <SelectTrigger
        size="sm"
        aria-label={ariaLabel}
        className={cn(
          //  `dark:bg-transparent`: `SelectTrigger` gốc có `dark:bg-input/30`,
          //  không tắt thì ở nền tối mỗi hàng lại hiện một hộp xám — đúng thứ
          //  vừa bỏ đi ở nền sáng.
          'h-7 w-auto gap-1.5 border-0 bg-transparent text-sm shadow-none dark:bg-transparent',
          'hover:bg-accent/60 dark:hover:bg-accent/60',
          //  Kiểu CHIP tự mang đệm riêng nên trigger phải bỏ đệm, không thì
          //  giá trị hàng này thụt vào so với chip ở hàng Tag ngay trên.
          variant === 'chip' ? 'px-0' : 'px-1.5',
          //  Chỉ xem: giấu mũi tên, bỏ làm mờ — xem ghi chú ở `task-status-select`.
          disabled && 'disabled:cursor-default disabled:opacity-100 [&>svg:last-child]:hidden',
        )}
      >
        {/*  BẮT BUỘC bọc trong `SelectValue`, dù nội dung là của mình.
             Radix canh danh sách thả xuống theo ĐÚNG nút này (`position` mặc
             định là `item-aligned`); không có `SelectValue` thì nó không có mốc
             nào, khung thả xuống rơi về góc trái dưới cùng — ở panel chi tiết
             là rơi hẳn ra ngoài màn hình, bấm vào ô chọn tưởng như bị khóa. */}
        <SelectValue>
          {current ? (
            <ChipValue option={current} variant={variant} short />
          ) : (
            <span className="text-muted-foreground">{placeholder}</span>
          )}
        </SelectValue>
      </SelectTrigger>
      <SelectContent>
        {options.map((o) => (
          <SelectItem key={o.value} value={o.value}>
            <ChipValue option={o} variant={variant} />
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

function ChipValue({
  option,
  variant,
  short,
}: {
  option: ChipOption
  variant: 'chip' | 'dot'
  short?: boolean
}) {
  const text = short ? (option.short ?? option.label) : option.label

  if (!option.color) return <span>{text}</span>

  if (variant === 'dot') {
    return (
      <span className="flex items-center gap-1.5">
        <span className={cn('size-2 shrink-0 rounded-full', dotClass(option.color))} />
        {text}
      </span>
    )
  }

  return (
    <span className={cn('rounded px-1.5 py-0.5 text-xs font-medium', chipClass(option.color))}>
      {text}
    </span>
  )
}
