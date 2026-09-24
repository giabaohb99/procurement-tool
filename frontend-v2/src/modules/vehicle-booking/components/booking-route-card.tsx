import { Repeat, Route, Users } from 'lucide-react'
import type { ReactNode } from 'react'

import { Card } from '@/shared/ui/card'
import { TimelineItem } from '@/shared/ui/timeline-item'
import { cn } from '@/shared/utils/cn'
import { REQUEST_TYPE, type Stop, type VehicleBooking } from '../types/vehicle-booking'
import { formatStamp } from '../utils/booking-time-format'
import { BookingCardHeader, BookingInfoItem } from './booking-info-item'

/**
 * Thẻ LỘ TRÌNH — điểm đi · điểm dừng · điểm đến xếp trên một trục dọc, mỗi điểm
 * kèm mốc thời gian của chính nó.
 *
 * Bản trước tách làm hai lưới rời nhau: "Điểm đi / Điểm đến" ở trên, "Thời gian
 * đi / Thời gian về" ở dưới, điểm dừng chen vào giữa. Người đọc phải tự ghép
 * ô 1 với ô 3 mới biết mấy giờ đi từ đâu — trong khi một chuyến xe vốn là một
 * đường thẳng có thứ tự, vẽ đúng hình của nó thì không phải ghép gì cả.
 */
export function BookingRouteCard({ booking }: { booking: VehicleBooking }) {
  const isDelivery = booking.request_type === REQUEST_TYPE.delivery
  const stops = booking.stops.filter((stop) => stop.location || stop.contact_name || stop.notes)

  return (
    <Card className="flex flex-col gap-4 p-5 pb-4">
      <BookingCardHeader
        icon={<Route className="size-5 text-sky-600 dark:text-sky-400" />}
        extra={
          <>
            {!isDelivery && booking.is_round_trip && (
              <Chip>
                <Repeat className="size-3" />
                Khứ hồi
              </Chip>
            )}
            {stops.length > 0 && <Chip>{stops.length} điểm dừng</Chip>}
          </>
        }
      >
        Lộ trình
      </BookingCardHeader>

      <ol className="flex flex-col">
        <TimelineItem marker={<Dot className="border-2 border-sky-500 bg-background" />}>
          <Waypoint
            label={isDelivery ? 'Điểm lấy hàng' : 'Điểm đi'}
            place={booking.start_location}
            time={formatStamp(booking.start_time)}
          />
        </TimelineItem>

        {stops.map((stop, index) => (
          <TimelineItem key={index} marker={<Dot className="bg-border" small />}>
            <StopLine stop={stop} />
          </TimelineItem>
        ))}

        <TimelineItem last marker={<Dot className="bg-sky-500" />}>
          <Waypoint
            label={isDelivery ? 'Điểm giao hàng' : 'Điểm đến'}
            place={booking.end_location}
            time={formatStamp(booking.end_time)}
            timeNote={isDelivery ? 'dự kiến giao' : 'dự kiến về'}
          />
        </TimelineItem>
      </ol>

      {/*  Chuyến CHỞ NGƯỜI: số khách + liên hệ + danh sách người đi. Giao hàng có
          thẻ riêng (người gửi / người nhận / hàng hóa) nên không chen vào đây.

          ⚠️ Ô nào RỖNG thì BỎ HẲN, không bày "—". Ở màn xem, một dòng "Người
          tham gia —" không nói thêm được gì so với không có dòng đó, mà vẫn
          chiếm đúng bằng chỗ của một dòng có thật. */}
      {!isDelivery && (booking.passenger_count > 0 || booking.contact_phone || booking.attendees) && (
        <div className="grid gap-4 border-t pt-4 sm:grid-cols-2">
          {booking.passenger_count > 0 && (
            <BookingInfoItem label="Số hành khách">
              <span className="inline-flex items-center gap-1.5">
                <Users className="size-3.5 text-muted-foreground" />
                {booking.passenger_count}
              </span>
            </BookingInfoItem>
          )}
          {booking.contact_phone && (
            <BookingInfoItem label="SĐT liên hệ">{booking.contact_phone}</BookingInfoItem>
          )}
          {booking.attendees && (
            <BookingInfoItem label="Người tham gia" className="sm:col-span-2">
              {booking.attendees}
            </BookingInfoItem>
          )}
        </div>
      )}
    </Card>
  )
}

/** Một đầu mút của lộ trình: nhãn nhỏ · địa điểm · mốc giờ. */
function Waypoint({
  label,
  place,
  time,
  timeNote,
}: {
  label: string
  place: string
  time: string
  timeNote?: string
}) {
  return (
    <div className="-mt-0.5 flex flex-col gap-0.5">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="text-sm font-medium leading-snug text-foreground">{place || '—'}</span>
      {time && (
        <span className="text-xs tabular-nums text-muted-foreground">
          {time}
          {timeNote ? ` · ${timeNote}` : ''}
        </span>
      )}
    </div>
  )
}

/** Điểm dừng trung gian: địa điểm + (người liên hệ · SĐT) + lý do dừng. */
function StopLine({ stop }: { stop: Stop }) {
  const contact = [stop.contact_name, stop.contact_phone].filter(Boolean).join(' · ')
  return (
    <div className="-mt-0.5 flex flex-col gap-0.5">
      <span className="text-sm leading-snug text-foreground">{stop.location || '—'}</span>
      {contact && <span className="text-xs text-muted-foreground">{contact}</span>}
      {stop.notes && <span className="text-xs italic text-muted-foreground">{stop.notes}</span>}
    </div>
  )
}

function Dot({ className, small }: { className?: string; small?: boolean }) {
  return (
    <span
      className={cn('mt-1.5 shrink-0 rounded-full', small ? 'size-2' : 'size-3', className)}
      aria-hidden="true"
    />
  )
}

/** Nhãn phụ nhỏ trên tiêu đề thẻ (Khứ hồi, số điểm dừng). */
function Chip({ children }: { children: ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full border bg-muted/40 px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
      {children}
    </span>
  )
}
