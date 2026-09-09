import type { Holiday, LeaveRequest } from '../types/leave'
import {
  buildWeekDays,
  holidayNamesOn,
  isWeekend,
  toISODate,
  WEEKDAY_LABELS,
} from '../utils/calendar-grid'
import { LeaveCalendarDayRow } from './leave-calendar-day-row'

interface LeaveCalendarWeekGridProps {
  anchor: Date
  requestsOn: (iso: string) => LeaveRequest[]
  holidays: Holiday[]
  todayISO: string
  /** Mở chế độ NGÀY cho hàng vừa bấm — lối thoát khi hàng quá đông. */
  onPickDay: (date: Date) => void
}

/**
 * Quá số này thì hàng ngang bắt đầu nuốt cả màn hình — phần dư gộp thành nút
 * "+N người nữa". Sáu chip vừa đủ một hàng trên màn 24" mà không xuống dòng.
 */
const MAX_VISIBLE = 6

/**
 * TUẦN — mỗi ngày một HÀNG NGANG, không phải một cột dọc. Lý do của hình dạng
 * đó nằm ở `LeaveCalendarDayRow`, nơi hàng được dựng (và cũng là nơi lo bố cục
 * khổ điện thoại).
 *
 * ⚠️ **Cắt ở sáu người.** "Tự giãn theo nội dung" nghe thì hay, cho tới hôm cả
 * phòng ba mươi người nghỉ chung: hàng đó tự dâng lên nuốt hết màn hình và sáu
 * ngày còn lại bị đẩy khỏi tầm nhìn — đúng cái tuần bận nhất lại là tuần không
 * xem được. Phần dư thành nút sang chế độ NGÀY.
 */
export function LeaveCalendarWeekGrid({
  anchor,
  requestsOn,
  holidays,
  todayISO,
  onPickDay,
}: LeaveCalendarWeekGridProps) {
  const days = buildWeekDays(anchor)
  const total = days.reduce((sum, d) => sum + requestsOn(toISODate(d)).length, 0)

  return (
    //  ⚠️ `max-md:flex-none` + `max-md:overflow-visible`: ở khổ hẹp trang bỏ chế
    //  độ `fill` nên CẢ TRANG cuộn. Giữ ô cuộn lồng bên trong thì vuốt trúng mép
    //  ngoài là trang không nhúc nhích — người dùng đọc ra là màn hình đơ.
    <div className="flex min-h-0 flex-1 flex-col overflow-auto rounded-md border max-md:flex-none max-md:overflow-visible">
      {total === 0 && (
        //  Nói ra một lần cho cả tuần. Bảy dòng "không ai nghỉ" nối nhau đọc như
        //  màn hình hỏng chứ không như một tuần yên ả.
        <p className="border-b bg-muted/30 px-4 py-2 text-sm text-muted-foreground">
          Cả tuần này không ai nghỉ.
        </p>
      )}

      {days.map((day, i) => {
        const iso = toISODate(day)
        return (
          <LeaveCalendarDayRow
            key={iso}
            date={day}
            weekdayLabel={WEEKDAY_LABELS[i]}
            items={requestsOn(iso)}
            holidayNames={holidayNamesOn(holidays, iso)}
            today={iso === todayISO}
            weekend={isWeekend(day)}
            onPick={onPickDay}
            maxVisible={MAX_VISIBLE}
            showEmptyNote
          />
        )
      })}
    </div>
  )
}
