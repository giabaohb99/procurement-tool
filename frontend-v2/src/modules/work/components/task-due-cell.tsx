import { CalendarDays, X } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { Calendar } from '@/shared/ui/calendar'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { cn } from '@/shared/utils/cn'
import { parseLocalDate, toDateInputValue } from '@/shared/utils/format-date'
import { addDays, dueTone, dueToneClass, formatDueLabel, today } from '../utils/due-date'

interface TaskDueCellProps {
  dueDate: string
  done: boolean
  canEdit: boolean
  onChange: (dueDate: string) => void
  /** Tên mốc, đọc lên cho trình đọc màn hình. Mặc định «Hạn chót». */
  label?: string
  /**
   * Tô màu theo mức KHẨN (quá hạn đỏ, sắp tới cam). Tắt cho NGÀY BẮT ĐẦU: ngày
   * bắt đầu đã trôi qua là chuyện hoàn toàn bình thường, tô đỏ nó thì cả cột
   * đỏ rực và người dùng học cách phớt lờ luôn cả màu đỏ thật ở cột hạn.
   */
  tone?: boolean
}

/**
 * Ô MỘT MỐC NGÀY sửa ngay trên dòng danh sách — dùng cho cả hạn chót lẫn ngày
 * bắt đầu.
 *
 * Khác `TaskDateRow` của panel chi tiết ở chỗ chỉ lo MỘT mốc và phải vừa một ô
 * bảng, nên không bày ba nút «Hôm nay · Ngày mai · Khác» ra hàng — chúng nằm
 * trong popover. Ô rỗng vẫn chiếm đủ chiều cao và hiện icon lịch mờ khi rê
 * chuột: không có gì để bấm thì người dùng không đoán được là sửa được tại chỗ.
 */
export function TaskDueCell({
  dueDate,
  done,
  canEdit,
  onChange,
  label = 'Hạn chót',
  tone = true,
}: TaskDueCellProps) {
  const [open, setOpen] = useState(false)
  const toneClass = tone ? dueToneClass(dueTone(dueDate, done)) : 'text-foreground'

  function pick(value: string) {
    onChange(value)
    setOpen(false)
  }

  if (!canEdit) {
    return dueDate ? (
      <span className={cn('text-xs', toneClass)}>{formatDueLabel(dueDate)}</span>
    ) : (
      <span className="text-xs text-muted-foreground">—</span>
    )
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          type="button"
          aria-label={dueDate ? `${label} ${formatDueLabel(dueDate)}` : `Đặt ${label.toLowerCase()}`}
          onClick={(e) => e.stopPropagation()}
          className={cn(
            'flex h-6 w-full items-center gap-1 rounded px-1 text-left text-xs hover:bg-accent',
            dueDate ? toneClass : 'text-muted-foreground',
          )}
        >
          {dueDate ? (
            formatDueLabel(dueDate)
          ) : (
            <CalendarDays className="size-3.5 opacity-0 transition-opacity group-hover/row:opacity-60" />
          )}
        </button>
      </PopoverTrigger>

      <PopoverContent align="start" className="w-auto p-2" onClick={(e) => e.stopPropagation()}>
        <div className="mb-2 flex items-center gap-1">
          <Button size="sm" variant="ghost" className="h-7 px-2" onClick={() => pick(today())}>
            Hôm nay
          </Button>
          <Button size="sm" variant="ghost" className="h-7 px-2" onClick={() => pick(addDays(1))}>
            Ngày mai
          </Button>
          {dueDate && (
            <Button
              size="sm"
              variant="ghost"
              className="h-7 px-2 text-muted-foreground"
              onClick={() => pick('')}
            >
              <X className="size-3.5" />
              Xóa
            </Button>
          )}
        </div>
        <Calendar
          mode="single"
          selected={dueDate ? parseLocalDate(dueDate) : undefined}
          onSelect={(d) => pick(d ? toDateInputValue(d) : '')}
        />
      </PopoverContent>
    </Popover>
  )
}
