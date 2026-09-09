import { AlertTriangle, MessageSquare } from 'lucide-react'

import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { formatDateTime } from '@/shared/utils/format-date'
import { useMeetingRooms } from '../hooks/use-room'
import { ROOM_BOOKING_STATUS, type RoomBooking } from '../types/room'

/**
 * CỘT PHẢI của phiếu đã gửi duyệt — «phiếu này đang ở đâu».
 *
 * Bản chỉ-xem trước đây bỏ trống cả nửa phải màn hình trong khi mấy thứ người
 * đọc cần lại nằm rải rác: trạng thái ở thanh tiêu đề, ý kiến người duyệt ở một
 * thẻ riêng bên dưới, mốc thời gian thì không có. Gom về một chỗ.
 *
 * ⚠️ **Hai dòng «Trạng thái» và «Số phiếu» đã BỎ (09/09/2026).** Cả hai chép lại
 * đúng cái đang nằm ở đầu trang: huy hiệu trạng thái nay đứng cạnh tiêu đề, còn
 * tiêu đề thì đọc thẳng là «Phiếu PH113». Mà đầu trang là dải GHIM, tức hai thứ
 * đó luôn trong tầm mắt — chép xuống đây không phải "gom về một chỗ" mà là nói
 * hai lần trên cùng một khung hình. Ở khổ 390px thẻ này rơi xuống dưới bản tóm
 * tắt, và bốn dòng của nó thì ba dòng là bản sao.
 *
 * Thứ còn lại đều là thứ KHÔNG có ở đâu khác: mốc thời gian, phiếu có đang chạy
 * trong luồng nhiều bước không, cảnh báo quá sức chứa, và ý kiến người duyệt.
 */
export function RoomBookingStatusPanel({ booking }: { booking: RoomBooking }) {
  const { data: roomData } = useMeetingRooms()
  const room = roomData?.items.find((r) => r.id === booking.room_id)
  const isOverCapacity = Boolean(
    room?.capacity && booking.attendee_count > room.capacity,
  )

  return (
    <div className="space-y-4 lg:sticky lg:top-20">
      <Card className="max-md:gap-3 max-md:py-4">
        {/*  `md:pb-3` chứ không phải `pb-3` + `max-md:pb-0`: ở khổ hẹp `Card` đã
             khai `gap-3`, cộng thêm đệm dưới của tiêu đề nữa là thành 24px cho
             một khe. Khai theo chiều dương thì không có hai lớp chồng nhau để
             phải gỡ bằng dấu `!`. */}
        <CardHeader className="max-md:px-4 md:pb-3">
          <CardTitle className="text-base">Tình trạng phiếu</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm max-md:px-4">
          {booking.submitted_at ? (
            <Row label="Gửi duyệt" value={formatDateTime(booking.submitted_at)} />
          ) : null}

          {booking.decided_at ? (
            <Row
              //  Nhãn đổi theo KẾT CỤC: «Quyết định lúc» cho một phiếu bị hủy
              //  đọc như thể ai đó đã ký nó.
              label={
                booking.status === ROOM_BOOKING_STATUS.CANCELLED ? 'Hủy lúc' : 'Quyết định lúc'
              }
              value={formatDateTime(booking.decided_at)}
            />
          ) : null}

          {/*  Phiếu chạy trong luồng nhiều bước thì nói ra, để người đọc biết
               nút duyệt nằm ở màn Phê duyệt chứ không phải ở đây. */}
          {booking.approval_instance_id > 0 &&
            booking.status === ROOM_BOOKING_STATUS.PENDING && (
              <p className="rounded-md bg-muted/50 p-2 text-xs text-muted-foreground">
                Phiếu đang chạy trong luồng phê duyệt nhiều bước.
              </p>
            )}

          {isOverCapacity && (
            <p className="flex items-start gap-1.5 rounded-md border border-destructive/40 bg-destructive/10 p-2 text-xs text-destructive">
              <AlertTriangle className="mt-px size-3.5 shrink-0" />
              Số người dự ({booking.attendee_count}) vượt sức chứa của {room?.name} (
              {room?.capacity} chỗ).
            </p>
          )}
        </CardContent>
      </Card>

      {/*  Ý kiến người duyệt đứng CẠNH trạng thái sinh ra nó, không nằm ở một
           thẻ lạc lõng giữa trang. */}
      {booking.decision_note ? (
        <Card className="max-md:gap-3 max-md:py-4">
          {/*  `md:pb-3` chứ không phải `pb-3` + `max-md:pb-0`: ở khổ hẹp `Card` đã
             khai `gap-3`, cộng thêm đệm dưới của tiêu đề nữa là thành 24px cho
             một khe. Khai theo chiều dương thì không có hai lớp chồng nhau để
             phải gỡ bằng dấu `!`. */}
        <CardHeader className="max-md:px-4 md:pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <MessageSquare className="size-4 text-muted-foreground" />
              Ý kiến người duyệt
            </CardTitle>
          </CardHeader>
          <CardContent className="max-md:px-4">
            <p className="text-sm whitespace-pre-wrap">{booking.decision_note}</p>
          </CardContent>
        </Card>
      ) : null}
    </div>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-muted-foreground">{label}</span>
      <span className="min-w-0 truncate text-right font-medium tabular-nums">{value}</span>
    </div>
  )
}
