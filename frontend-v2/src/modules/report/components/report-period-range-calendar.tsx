import { useState } from 'react'

import { Calendar } from '@/shared/ui/calendar'
import { RANGE_CLASS_NAMES } from '@/shared/ui/date-range-picker'
import { parseLocalDate, toDateInputValue } from '@/shared/utils/format-date'

interface ReportPeriodRangeCalendarProps {
  /** Khoảng đang HIỆN trên lịch (kỳ đã áp dụng, hoặc "Tùy chọn" vừa bấm). */
  from: string
  to: string
  /** Bấm một ngày — cha quyết định việc chuyển `preset` sang `'custom'`. */
  onPick: (from: string, to: string) => void
}

/**
 * Lịch 2 tháng bên trong popover kỳ (`ReportPeriodControl`) — chọn ngày là
 * chuyển thẳng sang "Tùy chọn khoảng ngày", KHÔNG có nút "Áp dụng" riêng của
 * chính nó (khác `DateRangePicker` gốc): popover CHA đã có "Áp dụng"/"Hủy"
 * chung cho cả preset lẫn so sánh, thêm một cấp xác nhận nữa là thừa.
 *
 * Hai nhịp chọn (`pickingEnd`) và lý do KHÔNG tin thẳng `mode="range"` của
 * react-day-picker — xem chú thích đầy đủ ở `shared/ui/date-range-picker.tsx`,
 * đây là bản rút gọn của đúng cơ chế đó.
 */
const REPORT_RANGE_MIDDLE = 'bg-primary/10 [&>button]:bg-transparent [&>button]:text-foreground'

export function ReportPeriodRangeCalendar({ from, to, onPick }: ReportPeriodRangeCalendarProps) {
  const [pickingEnd, setPickingEnd] = useState(false)
  const start = parseLocalDate(from)
  const end = parseLocalDate(to)
  const selected = start ? { from: start, to: end } : undefined

  function pickDay(clicked: Date | undefined) {
    if (!clicked) return
    if (!pickingEnd || !start) {
      onPick(toDateInputValue(clicked), '')
      setPickingEnd(true)
      return
    }
    const isReversed = clicked.getTime() < start.getTime()
    onPick(
      toDateInputValue(isReversed ? clicked : start),
      toDateInputValue(isReversed ? start : clicked),
    )
    setPickingEnd(false)
  }

  return (
    <Calendar
      mode="range"
      numberOfMonths={2}
      defaultMonth={start}
      selected={selected}
      onSelect={(_range, clicked) => pickDay(clicked)}
      //  Kiểu Haravan: hai đầu tô đậm, phần giữa là MỘT dải nhạt liền mạch.
      //  Bỏ `mt-1` giữa các tuần (dải vỡ thành từng hàng rời) và ẩn ngày của
      //  tháng kề bên (kỳ "Năm nay" tô cả ngày 29–31/12 lẫn 1/3 trông như lỗi).
      showOutsideDays={false}
      classNames={{ ...RANGE_CLASS_NAMES, week: 'flex w-full', range_middle: REPORT_RANGE_MIDDLE }}
    />
  )
}
