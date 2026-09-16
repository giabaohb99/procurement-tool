import { ChevronLeft, ChevronRight } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'

import { CALENDAR_VIEWS, type CalendarViewType } from '../utils/calendar-views'
import { BookingCalendarLegend } from './booking-calendar-legend'

interface BookingCalendarToolbarProps {
  /** Nhãn khoảng đang xem, lấy từ `view.title` của FullCalendar. */
  title: string
  view: CalendarViewType
  onViewChange: (view: CalendarViewType) => void
  onPrev: () => void
  onNext: () => void
  onToday: () => void
}

/**
 * Thanh tiêu đề của lịch đặt xe — TỰ DỰNG, không dùng `headerToolbar` của
 * FullCalendar (`headerToolbar={false}` ở trang).
 *
 * Bản cũ dùng thanh của FC và phải nắn bằng một chuỗi lớp `[&_.fc-*]`: nút chạy
 * theo bộ biến `--fc-button-*` nên không khớp `Button` của hệ thiết kế, chú giải
 * phải chèn thành hàng riêng bên trên nên bị ép sát mép thẻ, và tiêu đề chiếm
 * trọn một hàng ngang trong khi giữa bỏ trống. Dựng tay thì gom được cả ba khối
 * vào MỘT hàng và dùng đúng `Button` chuẩn.
 *
 * Bố cục: [‹ ›] [Hôm nay] · Tháng … ————— chú giải (dạt phải, tự xuống hàng khi
 * hẹp nhờ `flex-wrap` ở khối ngoài).
 */
export function BookingCalendarToolbar({
  title,
  view,
  onViewChange,
  onPrev,
  onNext,
  onToday,
}: BookingCalendarToolbarProps) {
  return (
    <div className="mb-2 flex flex-wrap items-center gap-x-4 gap-y-2 px-1">
      <div className="flex items-center gap-2">
        {/*  Hai nút mũi tên dính liền thành một cặp — chúng là một cặp thao tác,
            tách rời ra thì mắt phải tìm lại vị trí mỗi lần đổi tháng. */}
        <div className="flex items-center">
          <Button
            variant="outline"
            size="icon-sm"
            onClick={onPrev}
            aria-label="Tháng trước"
            className="rounded-r-none"
          >
            <ChevronLeft />
          </Button>
          <Button
            variant="outline"
            size="icon-sm"
            onClick={onNext}
            aria-label="Tháng sau"
            className="-ml-px rounded-l-none"
          >
            <ChevronRight />
          </Button>
        </div>
        <Button variant="outline" size="sm" onClick={onToday}>
          Hôm nay
        </Button>
        {/*  `first-letter:uppercase` vì locale vi của FC trả "tháng 9 năm 2026". */}
        <h2 className="ml-1 text-lg font-semibold first-letter:uppercase">{title}</h2>
      </div>

      <BookingCalendarLegend className="ml-auto" />

      {/*  Bộ chọn Ngày · Tuần · Tháng — ô CHỌN, đặt cuối hàng, đúng chỗ Google
          Calendar để nó. Bản trước dựng ba nút dán liền (segmented), nhưng ba nút
          chiếm chỗ giữa hàng và đẩy hàng chú giải xuống dòng thứ hai. */}
      <Select value={view} onValueChange={(next) => onViewChange(next as CalendarViewType)}>
        <SelectTrigger size="sm" className="w-[104px]" aria-label="Kiểu xem lịch">
          <SelectValue />
        </SelectTrigger>
        <SelectContent align="end">
          {CALENDAR_VIEWS.map((v) => (
            <SelectItem key={v.value} value={v.value}>
              {v.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}
