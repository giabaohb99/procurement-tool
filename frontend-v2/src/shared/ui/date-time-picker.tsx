import { useMemo } from 'react'
import { Clock } from 'lucide-react'

import { DatePicker } from '@/shared/ui/date-picker'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { cn } from '@/shared/utils/cn'
import { toDateInputValue } from '@/shared/utils/format-date'

/**
 * Ô chọn NGÀY + GIỜ — lịch của hệ thống ghép với danh sách giờ.
 *
 * Thay cho `<input type="datetime-local">`. Ô đó là widget của trình duyệt:
 * mỗi hệ điều hành vẽ một kiểu, không nhận được bộ giao diện chung (viền, nền,
 * chữ, chế độ tối đều trượt ra ngoài), trên Windows hiện `mm/dd/yyyy` trong khi
 * cả hệ dùng `dd/mm/yyyy`, và cái nút lịch tí xíu ở mép phải là thứ duy nhất mở
 * được bộ chọn — còn lại phải gõ mò qua sáu ô số. Cùng lý lẽ đã bỏ
 * `<input type="date">` để làm `DatePicker`.
 *
 * ⚠️ **Giá trị vào/ra giữ NGUYÊN dạng cũ** `YYYY-MM-DDTHH:mm` (giờ ĐỊA PHƯƠNG,
 * không phải ISO/UTC) nên chỗ gọi không phải đổi gì. Đừng "tiện tay" đổi sang
 * `Date` hay `toISOString()`: máy chạy ở UTC+7, `toISOString()` trừ đi 7 giờ và
 * cuộc họp đầu giờ nhảy sang hôm trước — xem `modules/hr/utils/room-time.ts`.
 */

/** `2026-09-10T09:00` → `['2026-09-10', '09:00']`. Rỗng thì trả hai chuỗi rỗng. */
export function splitDateTime(value: string): [string, string] {
  if (!value) return ['', '']
  const [date = '', time = ''] = value.split('T')
  //  Cắt còn `HH:mm`: API trả kèm giây (`09:00:00`), mà danh sách giờ khai theo
  //  phút — không cắt thì không mục nào khớp và ô hiện ra như chưa chọn.
  return [date, time.slice(0, 5)]
}

/** Ghép lại; thiếu một trong hai vế thì coi như CHƯA CHỌN, trả chuỗi rỗng. */
export function joinDateTime(date: string, time: string): string {
  if (!date || !time) return ''
  return `${date}T${time}`
}

/** Mọi mốc giờ trong ngày theo bước `step` phút — `['00:00', '00:15', …]`. */
export function buildTimeOptions(step: number): string[] {
  const out: string[] = []
  for (let minutes = 0; minutes < 24 * 60; minutes += step) {
    const hh = String(Math.floor(minutes / 60)).padStart(2, '0')
    const mm = String(minutes % 60).padStart(2, '0')
    out.push(`${hh}:${mm}`)
  }
  return out
}

interface DateTimePickerProps {
  /** `YYYY-MM-DDTHH:mm` — rỗng là chưa chọn. */
  value: string
  onChange: (value: string) => void
  disabled?: boolean
  /** Bước phút của danh sách giờ. Mặc định 15 — không ai đặt phòng lúc 14:37. */
  minuteStep?: number
  /** Giờ điền sẵn khi người dùng chọn NGÀY trước mà chưa chọn giờ. */
  defaultTime?: string
  /** Tên của cả cụm cho trình đọc màn hình (vd «Bắt đầu»). */
  label?: string
  className?: string
}

export function DateTimePicker({
  value,
  onChange,
  disabled,
  minuteStep = 15,
  defaultTime = '08:00',
  label,
  className,
}: DateTimePickerProps) {
  const [date, time] = splitDateTime(value)

  const options = useMemo(() => {
    const base = buildTimeOptions(minuteStep)
    //  Giá trị đang lưu KHÔNG rơi vào lưới (phiếu cũ đặt 09:05, hoặc bước phút
    //  đổi về sau) thì bù nó vào đúng thứ tự. Bỏ qua là ô rơi về chữ gợi ý,
    //  người dùng đọc ra "chưa chọn giờ" rồi chọn đại một mốc khác — giờ thật
    //  của cuộc họp bị ghi đè mà không ai thấy.
    if (time && !base.includes(time)) {
      return [...base, time].sort()
    }
    return base
  }, [minuteStep, time])

  return (
    <div role="group" aria-label={label} className={cn('flex gap-2', className)}>
      <DatePicker
        className="flex-1"
        value={date}
        //  Xóa ngày là xóa cả mốc: một cái giờ không có ngày thì không nói được
        //  điều gì, mà vẫn trông như đã điền.
        onChange={(next) => onChange(next ? joinDateTime(next, time || defaultTime) : '')}
        disabled={disabled}
      />

      <Select
        value={time}
        //  Chọn giờ trước khi chọn ngày thì lấy HÔM NAY — người dùng đang khai
        //  một cuộc họp, không phải một mốc trừu tượng.
        onValueChange={(next) => onChange(joinDateTime(date || toDateInputValue(new Date()), next))}
        disabled={disabled}
      >
        <SelectTrigger className="w-[7.5rem]" aria-label={label ? `Giờ ${label}` : 'Giờ'}>
          <Clock className="size-4 shrink-0 opacity-60" />
          <SelectValue placeholder="Giờ" />
        </SelectTrigger>
        <SelectContent className="max-h-72">
          {options.map((option) => (
            <SelectItem key={option} value={option}>
              {option}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}
