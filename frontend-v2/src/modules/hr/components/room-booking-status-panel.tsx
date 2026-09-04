import { AlertTriangle, MessageSquare } from 'lucide-react'

import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { formatDateTime } from '@/shared/utils/format-date'
import { useMeetingRooms } from '../hooks/use-room'
import { ROOM_BOOKING_STATUS, type RoomBooking } from '../types/room'
import { RoomStatusBadge } from './room-status-badge'

/**
 * CỘT PHẢI của phiếu đã gửi duyệt — «phiếu này đang ở đâu».
 *
 * Bản chỉ-xem trước đây bỏ trống cả nửa phải màn hình trong khi mấy thứ người
 * đọc cần lại nằm rải rác: trạng thái ở thanh tiêu đề, ý kiến người duyệt ở một
 * thẻ riêng bên dưới, mốc thời gian thì không có. Gom về một chỗ.
 */
export function RoomBookingStatusPanel({ booking }: { booking: RoomBooking }) {
  const { data: roomData } = useMeetingRooms()
  const room = roomData?.items.find((r) => r.id === booking.room_id)
  const isOverCapacity = Boolean(
    room?.capacity && booking.attendee_count > room.capacity,
  )

  return (
    <div className="space-y-4 lg:sticky lg:top-20">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Tình trạng phiếu</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="flex items-center justify-between gap-3">
            <span className="text-muted-foreground">Trạng thái</span>
            <RoomStatusBadge status={booking.status} label={booking.status_label} />
          </div>

          <Row label="Số phiếu" value={booking.code} />

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
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <MessageSquare className="size-4 text-muted-foreground" />
              Ý kiến người duyệt
            </CardTitle>
          </CardHeader>
          <CardContent>
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
