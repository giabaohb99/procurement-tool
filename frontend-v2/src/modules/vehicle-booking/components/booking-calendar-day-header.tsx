import { cn } from '@/shared/utils/cn'

interface BookingCalendarDayHeaderProps {
  /** Tên thứ do FullCalendar dựng theo `dayHeaderFormat` — "Thứ Tư" / "Th 4". */
  weekday: string
  /** Ngày trong tháng, bày thành con số to dưới tên thứ. */
  dayOfMonth: number
  isToday: boolean
}

/**
 * Tiêu đề CỘT NGÀY của khám Ngày · Tuần (có trục giờ).
 *
 * Mặc định FC chỉ in một dòng chữ. Ở khám NGÀY, dòng đó trải hết bề ngang lịch
 * (~1200px) nên màn hình mở ra là một thanh trống trơn với mỗi chữ "THỨ TƯ" bé
 * xíu nằm giữa — không nói ngày mấy, mà chỗ duy nhất nói là nhãn trên thanh
 * công cụ, tận đầu kia của thẻ.
 *
 * Dáng lấy theo Google Calendar: tên thứ nhỏ ở trên, con số ngày to ở dưới; hôm
 * nay thì CẢ HAI đổi màu nhấn và con số nằm trong vòng tròn đặc — cùng dấu hiệu
 * với ô "hôm nay" ở khám Tháng, để ba khám đọc ra như một.
 */
export function BookingCalendarDayHeader({
  weekday,
  dayOfMonth,
  isToday,
}: BookingCalendarDayHeaderProps) {
  return (
    <span className="flex flex-col items-center gap-0.5 py-0.5">
      <span className={cn(isToday && 'text-primary')}>{weekday}</span>
      <span
        className={cn(
          //  Con số phải tự khai cỡ + màu: thẻ cha `.fc-col-header-cell-cushion`
          //  đang bị ghim 11px/muted cho tên thứ, và kế thừa thì thua khai trực tiếp.
          //
          //  CÙNG MỘT CỠ cho cả khám Ngày lẫn khám Tuần — đo lại hai ảnh mẫu của
          //  Google Calendar thì vòng tròn hai bên bằng nhau (~44px). Bản trước
          //  thu nhỏ ở khám Tuần cho "đỡ chật", nhưng 7 cột rộng ~175px thừa sức
          //  chứa, mà hai khám lệch cỡ thì lúc đổi qua lại con số nhảy giật.
          'grid size-11 place-items-center rounded-full text-[26px] font-normal tracking-normal',
          isToday ? 'bg-primary text-primary-foreground' : 'text-foreground',
        )}
      >
        {dayOfMonth}
      </span>
    </span>
  )
}
