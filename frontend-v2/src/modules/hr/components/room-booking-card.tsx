import { CalendarDays, ChevronRight, DoorClosed, MessageSquareWarning } from 'lucide-react'

import { formatDate, formatDateTime } from '@/shared/utils/format-date'
import type { RoomBooking } from '../types/room'
import { formatTimeRange } from '../utils/room-time'
import { RoomStatusBadge } from './room-status-badge'

interface RoomBookingCardProps {
  booking: RoomBooking
  /**
   * Bày huy hiệu trạng thái không. Tab «Cần tôi duyệt» tắt: mọi phiếu ở đó đều
   * là «Chờ duyệt», một huy hiệu lặp lại y hệt trên từng thẻ chỉ ăn chỗ của
   * dòng chữ đứng cạnh nó — cùng lý do với `LeaveRequestCard`.
   */
  showStatus?: boolean
  /** Hạn xử lý việc duyệt — chỉ tab «Cần tôi duyệt» có. */
  dueAt?: string | null
}

/**
 * Một phiếu đặt phòng ở chế độ MÀN HẸP — xem `DataTableProps.mobileCard`.
 *
 * ⚠️ **Thứ tự trong thẻ không phải thứ tự cột của bảng.** Bảng xếp «Số phiếu»
 * trước vì cột đầu là cột định danh và nó được ghim; trên thẻ thì mã phiếu là
 * thứ ÍT dùng nhất — người ta nhận ra phiếu bằng NỘI DUNG CUỘC HỌP, còn mã chỉ
 * dùng khi đọc số cho nhau qua điện thoại. Nên nội dung lên đầu, mã tụt xuống
 * dòng chân cùng cỡ chữ nhỏ.
 *
 * ⚠️ **PHÒNG và GIỜ là hai dòng riêng, không gộp một dòng cho gọn.** Đây là hai
 * câu trả lời khác nhau (*ở đâu* · *lúc nào*) và cũng là hai thứ va nhau khi
 * trùng lịch. Gộp lại thì trên máy 390px chúng tự ngắt ở chỗ ngẫu nhiên, và
 * đúng nửa sau — khung giờ — là phần hay rơi xuống dòng dưới nhất.
 *
 * ⚠️ **Không tooltip trong thẻ.** Màn cảm ứng không có nhịp «rê chuột», nên lý
 * do bị từ chối / trả về hiện thẳng thành chữ.
 */
export function RoomBookingCard({
  booking,
  showStatus = true,
  dueAt,
}: RoomBookingCardProps) {
  return (
    <div className="flex items-start gap-2">
      <div className="min-w-0 flex-1 space-y-1.5">
        {/*  Hàng đầu: thứ ĐỊNH DANH phiếu + trạng thái. Phiếu chưa đặt tên cuộc
             họp thì lấy mã thay, không để trống một dòng đầu.
             `min-w-0` + `line-clamp-2` trên khối bên trái — thiếu nó thì tiêu đề
             dài đẩy huy hiệu tràn ra ngoài mép thẻ. Chặn hai dòng vì `title`
             không giới hạn độ dài ở tầng nhập. */}
        <div className="flex items-start justify-between gap-2">
          <span className="line-clamp-2 min-w-0 font-medium break-words text-foreground">
            {booking.title || booking.code}
          </span>
          {showStatus && (
            <span className="shrink-0">
              <RoomStatusBadge status={booking.status} label={booking.status_label} />
            </span>
          )}
        </div>

        <p className="flex items-center gap-1.5 text-sm text-muted-foreground">
          <DoorClosed className="size-3.5 shrink-0" aria-hidden="true" />
          <span className="min-w-0 truncate">
            {booking.room_name || booking.room_code || `#${booking.room_id}`}
          </span>
        </p>

        {/*  Ngày + khung giờ đứng chung một dòng: hai vế của cùng một câu hỏi
             «họp lúc nào», tách hai dòng thì mắt phải ghép lại. */}
        <div className="flex flex-wrap items-center gap-x-1.5 gap-y-1 text-sm text-muted-foreground">
          <CalendarDays className="size-3.5 shrink-0" aria-hidden="true" />
          <span className="tabular-nums">{formatDate(booking.start_at)}</span>
          <span className="font-medium tabular-nums text-foreground">
            <span aria-hidden="true">· </span>
            {formatTimeRange(booking.start_at, booking.end_at)}
          </span>
        </div>

        {booking.decision_note && (
          <p className="flex items-start gap-1 text-xs break-words text-muted-foreground">
            <MessageSquareWarning className="mt-0.5 size-3.5 shrink-0" aria-hidden="true" />
            <span>{booking.decision_note}</span>
          </p>
        )}

        {/*  Dòng chân: mã phiếu · người đặt · hạn xử lý. Ba thứ đều là chữ nhỏ
             vì chúng chỉ dùng để đối chiếu, không để nhận ra phiếu. */}
        <div className="flex flex-wrap items-center gap-x-2 text-xs text-muted-foreground">
          <span className="tabular-nums">{booking.code}</span>
          {booking.requester_name && (
            <>
              <span aria-hidden="true">·</span>
              <span className="min-w-0 truncate">{booking.requester_name}</span>
            </>
          )}
          {dueAt && (
            <>
              <span aria-hidden="true">·</span>
              <span className="tabular-nums">Hạn xử lý {formatDateTime(dueAt)}</span>
            </>
          )}
        </div>
      </div>

      {/*  Mũi tên nói THẺ NÀY BẤM ĐƯỢC. Trên bảng, con trỏ đổi hình khi rê qua
           dòng đã nói điều đó; màn cảm ứng không có con trỏ nên phải nói bằng
           hình. */}
      <ChevronRight className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
    </div>
  )
}
