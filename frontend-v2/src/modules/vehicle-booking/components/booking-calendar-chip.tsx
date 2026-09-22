import { Ban, CalendarClock, MapPin, TriangleAlert, User, UserCog } from 'lucide-react'

import { HoverCard, HoverCardContent, HoverCardTrigger } from '@/shared/ui/hover-card'
import { cn } from '@/shared/utils/cn'

import type { TimelineEvent } from '../api/vehicle-booking-timeline-api'
import {
  BOOKING_STATUS,
  BOOKING_STATUS_BADGE,
  REQUEST_TYPE,
  bookingStatusLabel,
} from '../types/vehicle-booking'
import { formatBookingRange, timeOf } from '../utils/booking-time-format'
import { calendarStatusStyle, needsDispatch } from '../utils/calendar-status-colors'
import { CarBookingIcon, DeliveryBookingIcon } from './booking-type-icons'
import { StatusPill } from './status-pill'

/** Một dòng thông tin trong thẻ hover — bỏ hẳn nếu không có giá trị. */
function DetailRow({ icon, children }: { icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="flex items-start gap-2 text-xs">
      <span className="mt-px shrink-0 text-muted-foreground">{icon}</span>
      <span className="min-w-0 break-words">{children}</span>
    </div>
  )
}

interface BookingCalendarChipProps {
  ev: TimelineEvent
  /**
   * Khám CÓ TRỤC GIỜ (Ngày · Tuần): chip phải cao bằng ô mà FullCalendar cấp —
   * đó mới là cách nó biểu đạt "chuyến này dài 3 tiếng". Khám Tháng thì cao cố
   * định 28px vì ô ngày không có thang giờ để bám.
   */
  fillHeight?: boolean
}

/**
 * Chip một chuyến xe trên lịch tháng — CAO MỘT DÒNG theo lối Google Calendar.
 *
 * Bản trước bày 4 dòng (mục đích · người tạo · tài xế · điểm đến) nên một ngày 3
 * chuyến đã đẩy hàng tuần cao hơn 300px, và các hàng trong tháng lệch nhau hẳn
 * một khoảng lớn. Chi tiết KHÔNG mất: nó chuyển vào thẻ hover — đúng cách
 * Google Calendar làm, và cũng là chỗ duy nhất đủ rộng để hiện lộ trình đầy đủ
 * mà không phải cắt chữ.
 *
 * MỌI chip đều nền đặc, không phân biệt chuyến trong ngày / nhiều ngày. Bản
 * trước để chuyến trong ngày nền TRONG SUỐT (chỉ chấm màu + chữ, đúng kiểu
 * Google Calendar) nhưng đặt cạnh thanh đặc của chuyến nhiều ngày thì nó trông
 * như chip chưa dựng xong — chữ trôi trên nền trắng, không có thân. Chuyến
 * nhiều ngày vẫn tự nhận ra vì nó TRẢI NGANG nhiều cột, không cần thêm dấu hiệu.
 */
export function BookingCalendarChip({ ev, fillHeight = false }: BookingCalendarChipProps) {
  const style = calendarStatusStyle(ev.status)
  const isDelivery = ev.request_type === REQUEST_TYPE.delivery
  const Icon = isDelivery ? DeliveryBookingIcon : CarBookingIcon
  const time = timeOf(ev.start_time)
  const title = ev.purpose || ev.request_type_label
  const undispatched = needsDispatch(ev.assigned_driver_label, ev.assigned_vehicle_label)
  const dispatchLabel = undispatched
    ? 'Chưa điều phối'
    : [ev.assigned_driver_label, ev.assigned_vehicle_label].filter(Boolean).join(' · ')
  const route = [ev.start_location, ev.end_location].filter(Boolean).join('  →  ')
  //  Phiếu ĐÃ HỦY / BỊ TỪ CHỐI: thẻ hover phải nói LÝ DO. Chip trên lịch chỉ
  //  gạch ngang chữ, nên không có nó thì người xem thấy một chuyến chết mà
  //  không biết vì sao — và câu trả lời nằm sau hai lần bấm (mở phiếu, cuộn tới
  //  thẻ tiến trình). Rỗng vẫn dựng dòng, xem `closeReasonFact`.
  const isClosed =
    ev.status === BOOKING_STATUS.cancelled || ev.status === BOOKING_STATUS.rejected
  const closeReason = ev.cancel_reason?.trim() || 'Không ghi lý do'

  return (
    <HoverCard openDelay={220} closeDelay={80}>
      <HoverCardTrigger asChild>
        <div
          className={cn(
            'flex w-full items-center gap-2 overflow-hidden rounded-[4px] px-2',
            //  Chuyến ngắn (30 phút) ra ô rất thấp → `items-start` để dòng chữ
            //  dính lên đỉnh thay vì bị cắt giữa; `min-h-0` cho nó co được.
            //
            //  Viền màu NỀN THẺ ở khám có trục giờ: hai chuyến trùng giờ được FC
            //  xếp chồng lấn nhau, mà cùng trạng thái thì cùng màu — không viền
            //  thì hai khối nhập làm một mảng đặc, chuyến nằm trên biến mất hẳn
            //  (chỉ còn mấy chữ giờ trôi giữa nền). Google Calendar tách khối
            //  đúng bằng cách này.
            //
            //  `border-card` chứ KHÔNG `border-white`: viền này đóng vai KHE HỞ
            //  giữa hai khối, nên nó phải là màu mặt thẻ. Ghim trắng thì nền tối
            //  hoá ra mỗi chuyến bị viền sáng quắc bao quanh.
            fillHeight ? 'h-full min-h-0 items-start border border-card py-1' : 'h-[28px]',
            //  KHÔNG dùng `leading-none` ở đây: line-height = đúng cỡ chữ, mà
            //  tiếng Việt xếp dấu CẢ TRÊN LẪN DƯỚI đường cơ sở ("Hồng Ngự",
            //  "Củ Chi") nên `overflow-hidden` của chip cắt mất phần dấu. 1.45
            //  chừa đủ chỗ cho cả hai tầng dấu.
            'text-[12.5px] leading-[1.45] text-white transition-[filter]',
            //  Sáng lên khi trỏ vào — dùng `brightness` vì nền là màu động (hex
            //  theo trạng thái), không đặt sẵn được bằng lớp `hover:bg-*`.
            'hover:brightness-110',
          )}
          //  Palette cố định khai bằng hex (xem `utils/calendar-status-colors`).
          style={{ backgroundColor: style.color }}
          title={undispatched ? 'Chưa điều phối' : dispatchLabel}
        >
          <Icon className="size-3.5 shrink-0" />
          {time && (
            <span className="shrink-0 font-semibold tabular-nums text-white/85">{time}</span>
          )}
          <span className={cn('truncate', style.strikethrough && 'line-through opacity-80')}>
            {title}
          </span>
          {/*  CHƯA ĐIỀU PHỐI: một dấu nhỏ ở cuối chip, thay cho viền nét đứt.
               Viền nét đứt bao quanh từng chip đã thử rồi bỏ — mỗi ô ngày vài
               khung gạch là lưới rối hẳn lên. Dấu này `shrink-0` nên luôn hiện,
               tiêu đề thu lại nhường chỗ: biết chuyến chưa có xe quan trọng hơn
               đọc trọn mấy ký tự cuối của mục đích. */}
          {undispatched && <TriangleAlert className="ml-auto size-3 shrink-0 text-white" />}
        </div>
      </HoverCardTrigger>

      <HoverCardContent align="start" className="w-80 space-y-2.5 p-3.5">
        <div className="space-y-1.5">
          <div className="flex items-start justify-between gap-2">
            <span className="flex min-w-0 items-center gap-1.5 text-sm font-semibold">
              <Icon className="size-3.5 shrink-0" style={{ color: style.color }} />
              <span className="min-w-0 break-words">{title}</span>
            </span>
            <StatusPill tone={BOOKING_STATUS_BADGE[ev.status] ?? 'gray'} className="shrink-0">
              {bookingStatusLabel(ev.status, ev.driver_status)}
            </StatusPill>
          </div>
          <p className="text-[11px] text-muted-foreground">
            {ev.code} · {ev.request_type_label}
          </p>
        </div>

        <div className="space-y-1.5 border-t pt-2.5">
          <DetailRow icon={<CalendarClock className="size-3.5" />}>
            {formatBookingRange(ev.start_time, ev.end_time)}
          </DetailRow>
          {ev.requester && (
            <DetailRow icon={<User className="size-3.5" />}>{ev.requester}</DetailRow>
          )}
          <DetailRow icon={<UserCog className="size-3.5" />}>
            {/*  Chưa có xe/tài xế là việc CÒN PHẢI LÀM — cho nó màu cảnh báo chứ
                 không để lẫn vào mấy dòng thông tin bình thường. */}
            <span className={cn(undispatched && 'font-medium text-amber-600 dark:text-amber-400')}>
              {dispatchLabel}
            </span>
          </DetailRow>
          {route && <DetailRow icon={<MapPin className="size-3.5" />}>{route}</DetailRow>}
        </div>

        {isClosed && (
          <div className="border-t pt-2.5">
            <DetailRow icon={<Ban className="size-3.5 text-destructive" />}>
              <span className="font-medium text-destructive">
                {bookingStatusLabel(ev.status, ev.driver_status)}:
              </span>{' '}
              <span className="break-words">{closeReason}</span>
            </DetailRow>
          </div>
        )}
      </HoverCardContent>
    </HoverCard>
  )
}
