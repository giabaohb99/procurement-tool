import { Ban, CheckCircle2, Circle } from 'lucide-react'

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { cn } from '@/shared/utils/cn'
import { WORK_STATUS_LABELS, WORK_TASK_STATUS } from '../types/work'

interface TaskStatusSelectProps {
  status: number
  disabled?: boolean
  /**
   * Bản GỌN cho ô của bảng — cùng khuôn `compact` mà `TaskAssigneePicker` và
   * `LabelFieldInput` đã dùng.
   *
   * Trong một dòng bảng, viên thuốc cỡ đầy đủ cao 28px đứng cạnh chữ 13px và ô
   * ngày trơn thì nó to lấn át cả dòng — khách chê *"nhìn to mất cân đối"*.
   * Ở panel chi tiết thì cỡ đầy đủ mới đúng: chỗ ấy nó là thứ người ta nhìn đầu
   * tiên ("xong chưa?"), thu nhỏ lại là mất luôn vai trò ấy.
   */
  compact?: boolean
  onChange: (status: number) => void
}

/**
 * Trạng thái việc — viên thuốc góc trên bên trái panel, không phải một hàng
 * thuộc tính như trước.
 *
 * Đây là thứ người ta nhìn đầu tiên khi mở một việc ("xong chưa?") nên nó phải
 * đứng ngang tiêu đề chứ không nằm lẫn giữa Cột / Độ ưu tiên / Tag. Màu mang
 * nghĩa: xanh = hoàn thành, xám gạch = đã hủy, còn lại là đang mở.
 */
export function TaskStatusSelect({
  status,
  disabled,
  compact = false,
  onChange,
}: TaskStatusSelectProps) {
  const tone = STATUS_TONE[status] ?? STATUS_TONE[WORK_TASK_STATUS.OPEN]
  const Icon = tone.icon

  return (
    <Select value={String(status)} disabled={disabled} onValueChange={(v) => onChange(Number(v))}>
      <SelectTrigger
        size="sm"
        aria-label="Trạng thái công việc"
        className={cn(
          'w-auto rounded-full border-0 py-0 font-medium shadow-none',
          //  ⚠️ Chiều cao phải ép bằng `!`. `SelectTrigger` gốc đặt cỡ bằng
          //  `data-[size=sm]:h-8` — chọn lọc của bộ chọn thuộc tính cao hơn một
          //  lớp `h-*` trần, nên `h-7` viết ở đây trước nay KHÔNG hề ăn: viên
          //  thuốc vẫn cao 32px ở mọi chỗ, đo ra mới biết.
          compact ? 'h-5! gap-1 px-2 text-[11px]' : 'h-7! gap-1.5 px-2.5 text-xs',
          //  Chỉ xem thì giấu mũi tên và bỏ vẻ "bấm được", nhưng KHÔNG làm mờ
          //  (`disabled:opacity-50` của bản gốc): viên thuốc này là thông tin,
          //  mờ đi thì đọc nhầm thành chữ gợi ý.
          disabled && 'disabled:cursor-default disabled:opacity-100 [&>svg:last-child]:hidden',
          tone.chip,
        )}
      >
        {/*  Bọc `SelectValue` để Radix có mốc canh khung thả xuống — xem ghi
             chú dài ở `task-chip-select.tsx`. */}
        <SelectValue>
          <Icon className={cn(compact ? 'size-3' : 'size-3.5', tone.text)} />
          {WORK_STATUS_LABELS[status] ?? 'Không rõ'}
        </SelectValue>
      </SelectTrigger>
      <SelectContent>
        {Object.entries(WORK_STATUS_LABELS).map(([value, label]) => (
          <SelectItem key={value} value={value}>
            {label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

//  Class viết đủ chữ, không ghép chuỗi — Tailwind quét mã theo văn bản.
//
//  Mỗi tông phải khai CẢ `dark:bg-…`: `SelectTrigger` gốc mang sẵn
//  `dark:bg-input/30`, không đè lên thì ở nền tối viên thuốc mất màu và trạng
//  thái «Hoàn thành» nhìn hệt «Đang mở».
const STATUS_TONE: Record<number, { chip: string; text: string; icon: typeof Circle }> = {
  [WORK_TASK_STATUS.OPEN]: {
    chip: 'bg-sky-500/10 text-sky-700 dark:bg-sky-500/15 dark:text-sky-300',
    text: 'text-sky-600 dark:text-sky-400',
    icon: Circle,
  },
  [WORK_TASK_STATUS.DONE]: {
    chip: 'bg-emerald-500/10 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300',
    text: 'text-emerald-600 dark:text-emerald-400',
    icon: CheckCircle2,
  },
  [WORK_TASK_STATUS.CANCELLED]: {
    chip: 'bg-slate-500/10 text-slate-600 line-through dark:bg-slate-500/20 dark:text-slate-300',
    text: 'text-slate-500',
    icon: Ban,
  },
}
