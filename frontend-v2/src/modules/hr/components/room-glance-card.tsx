import { ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Badge } from '@/shared/ui/badge'
import { ChartCard } from '@/shared/ui/chart'
import type { RoomGlance } from '../hooks/use-hr-room-glance'
import type { RoomBooking } from '../types/room'
import { formatTimeRange } from '../utils/room-time'

/** Số dòng bày ra; phần dư chỉ đếm lại thành một câu. */
const MAX_ROWS = 6

interface RoomGlanceCardProps {
  glance: RoomGlance
  /** Chốt "bây giờ" do trang truyền xuống — xem ghi chú ở `isOngoing`. */
  now: Date
  /** Ô span trên lưới của trang Tổng quan. */
  className?: string
}

/**
 * "Hôm nay phòng nào bận" — vế còn lại của cặp việc hành chính hằng ngày mà
 * phân hệ Nhân sự ôm: nghỉ phép và đặt phòng họp.
 *
 * Chỉ liệt kê phiếu ĐÃ DUYỆT, cùng lẽ với thẻ nghỉ phép: phiếu còn chờ ký chưa
 * giữ được phòng chắc chắn, xếp lịch theo nó là hẹn nhau vào một chỗ có thể mất.
 * Số phiếu đang chờ ký nằm ở dòng chân thẻ.
 */
export function RoomGlanceCard({ glance, now, className }: RoomGlanceCardProps) {
  if (!glance.canRead) {
    return (
      <ChartCard
        className={className}
        title="Lịch họp hôm nay"
        isEmpty
        emptyLabel="Bạn không có quyền xem phiếu đặt phòng."
      >
        <div />
      </ChartCard>
    )
  }

  const shown = glance.today.slice(0, MAX_ROWS)
  const rest = glance.today.length - shown.length

  return (
    // ⚠️ KHÔNG dùng `isEmpty` của `ChartCard`: nó thay THẲNG toàn bộ nội dung
    // bằng một câu, tức dòng chân thẻ biến mất theo — mà dòng chân mới là chỗ
    // ghi «n phiếu chờ duyệt». Hôm nào không có cuộc họp nào lại thường đúng là
    // hôm người duyệt rảnh để ký; giấu con số đó đi là giấu đúng lúc cần nhất.
    <ChartCard
      className={className}
      title="Lịch họp hôm nay"
      description="Phiếu đặt phòng đã duyệt, theo phạm vi bạn xem được."
      loading={glance.isLoading}
    >
      <div className="flex flex-1 flex-col">
        {glance.today.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">
            Hôm nay chưa có cuộc họp nào.
          </p>
        ) : (
          <ul className="divide-y">
            {shown.map((booking) => (
              <BookingRow key={booking.id} booking={booking} now={now} />
            ))}
          </ul>
        )}

        {rest > 0 && (
          <p className="pt-2.5 text-xs text-muted-foreground">Và {rest} cuộc nữa.</p>
        )}

        {/* `mt-auto` để cụm này luôn nằm đáy thẻ, kể cả khi thẻ bị kéo cao bằng
            thẻ cao nhất cùng hàng. */}
        <div className="mt-auto flex flex-wrap items-center gap-x-4 gap-y-1 pt-3 text-sm">
          <Link
            to={appRoutes.hr.roomCalendar}
            className="inline-flex items-center gap-1 font-medium text-primary hover:underline"
          >
            Mở lịch phòng họp
            <ArrowRight className="size-3.5" />
          </Link>

          {/* Số phiếu chờ ký KHÔNG lên dải thẻ số liệu như đơn nghỉ phép: đặt
              phòng là việc nhẹ hơn nhiều, một phiếu treo không kéo theo quỹ
              phép hay bảng lương. Nhưng vẫn phải nói ra, không thì người duyệt
              chỉ biết mình còn việc khi mở đúng màn đó. */}
          {glance.pending > 0 && (
            <Link
              to={appRoutes.hr.roomBookings}
              className="text-warning hover:underline"
            >
              {glance.pending} phiếu chờ duyệt
            </Link>
          )}
        </div>
      </div>
    </ChartCard>
  )
}

function BookingRow({ booking, now }: { booking: RoomBooking; now: Date }) {
  return (
    <li className="py-2.5 first:pt-0">
      <Link
        to={appRoutes.hr.roomBookingDetail(booking.id)}
        className="flex items-center justify-between gap-3 hover:underline"
      >
        <div className="min-w-0">
          <p className="flex items-center gap-1.5 text-sm font-medium">
            <span className="truncate">{booking.title || booking.code}</span>
            {isOngoing(booking, now) && (
              <Badge variant="secondary" className="shrink-0 text-[10px]">
                Đang họp
              </Badge>
            )}
          </p>
          <p className="truncate text-xs text-muted-foreground">
            {booking.room_name || booking.room_code} · {booking.requester_name}
          </p>
        </div>
        <span className="shrink-0 text-xs tabular-nums text-muted-foreground">
          {formatTimeRange(booking.start_at, booking.end_at)}
        </span>
      </Link>
    </li>
  )
}

/**
 * Cuộc họp đang diễn ra vào lúc `now`.
 *
 * Mốc "bây giờ" do NƠI GỌI truyền xuống chứ không tự `new Date()` trong hàm:
 * thẻ vẽ nhiều dòng, mỗi dòng tự lấy giờ riêng thì hai dòng sát nhau có thể
 * rơi vào hai phía của cùng một mốc kết thúc.
 */
function isOngoing(booking: RoomBooking, now: Date): boolean {
  const start = new Date(booking.start_at).getTime()
  const end = new Date(booking.end_at).getTime()
  const at = now.getTime()
  return start <= at && at < end
}
