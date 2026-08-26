import { CalendarRange, X } from 'lucide-react'
import { useState } from 'react'
import type { DateRange } from 'react-day-picker'

import { Button } from '@/shared/ui/button'
import { Calendar } from '@/shared/ui/calendar'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { cn } from '@/shared/utils/cn'

export interface DateRangePickerProps {
  /** `YYYY-MM-DD` — đúng dạng API nhận và trả. Rỗng = chưa chọn. */
  from?: string
  to?: string
  /** Gọi khi chọn xong hoặc xóa. Xóa thì trả hai chuỗi rỗng. */
  onChange: (from: string, to: string) => void
  placeholder?: string
  disabled?: boolean
  className?: string
}

/** `YYYY-MM-DD` theo giờ ĐỊA PHƯƠNG — `toISOString()` đổi sang UTC nên lệch ngày. */
function toDateString(day: Date): string {
  const thang = String(day.getMonth() + 1).padStart(2, '0')
  const ngay = String(day.getDate()).padStart(2, '0')
  return `${day.getFullYear()}-${thang}-${ngay}`
}

/** `"2026-09-11"` → `Date` giờ địa phương. Chuỗi rỗng / sai → `undefined`. */
function parseDate(raw?: string): Date | undefined {
  if (!raw) return undefined
  const day = new Date(`${raw}T00:00:00`)
  return Number.isNaN(day.getTime()) ? undefined : day
}

/** `"2026-09-11"` → `"11/09/2026"`. Người Việt đọc ngày trước, tháng sau. */
function display(raw?: string): string {
  const day = parseDate(raw)
  if (!day) return '…'
  return day.toLocaleDateString('vi-VN')
}

/**
 * Chọn KHOẢNG NGÀY bằng lịch hai tháng — bản `mode="range"` của `Calendar`.
 *
 * Khác `DateRangePresetPicker` (cũ) ở chỗ quan trọng: bản kia dùng hai ô
 * `<input type="date">`, mà ô nguyên bản hiện theo locale của MÁY nên máy đặt
 * tiếng Anh ra «mm/dd/yyyy» — người dùng gõ ngày Việt vào là sai tháng. Ở đây
 * chọn trên lịch nên không có chỗ để gõ nhầm, và nhãn hiện `dd/mm/yyyy`.
 *
 * Hai tháng cạnh nhau vì khoảng ngày hay vắt qua đầu tháng; một tháng thì phải
 * bấm mũi tên qua lại mới chọn xong một khoảng.
 *
 * Chỉ báo ra ngoài khi đã có **cả hai đầu** — khoảng nửa vời gửi lên backend là
 * số liệu nhảy một nhịp vô nghĩa ngay giữa lúc người dùng đang chọn.
 */
export function DateRangePicker({
  from,
  to,
  onChange,
  placeholder = 'Chọn khoảng ngày',
  disabled,
  className,
}: DateRangePickerProps) {
  const [open, setOpen] = useState(false)
  const selected = Boolean(from && to)

  const khoang: DateRange | undefined = parseDate(from)
    ? { from: parseDate(from), to: parseDate(to) }
    : undefined

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="outline"
          disabled={disabled}
          className={cn('w-auto min-w-56 justify-start gap-2 font-normal',
                        !selected && 'text-muted-foreground', className)}
        >
          <CalendarRange className="size-4 shrink-0 text-muted-foreground" />
          <span className="truncate">
            {selected ? `${display(from)} – ${display(to)}` : placeholder}
          </span>
          {selected && (
            <span
              role="button"
              tabIndex={-1}
              aria-label="Xóa khoảng ngày"
              className="ml-auto shrink-0 rounded-full p-0.5 text-muted-foreground hover:bg-muted hover:text-foreground"
              onClick={(event) => {
                //  Không để cú bấm nổi lên nút cha, nếu không nó mở luôn lịch
                //  ngay sau khi vừa xóa.
                event.stopPropagation()
                onChange('', '')
              }}
            >
              <X className="size-3.5" />
            </span>
          )}
        </Button>
      </PopoverTrigger>

      <PopoverContent className="w-auto p-0" align="start">
        <Calendar
          mode="range"
          numberOfMonths={2}
          defaultMonth={parseDate(from)}
          selected={khoang}
          onSelect={(next) => {
            if (!next?.from || !next?.to) return
            onChange(toDateString(next.from), toDateString(next.to))
            setOpen(false)
          }}
        />
      </PopoverContent>
    </Popover>
  )
}
