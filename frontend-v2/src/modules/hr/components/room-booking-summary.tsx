import { CalendarDays, Clock, DoorOpen, Users } from 'lucide-react'

import { formatDate } from '@/shared/utils/format-date'
import type { RoomBooking } from '../types/room'
import { formatTimeRange, minutesBetween } from '../utils/room-time'

/**
 * Phiếu đã gửi duyệt — bản CHỈ XEM.
 *
 * ⚠️ Không dựng lại form với cờ `disabled`, và cũng **không xếp tám ô
 * `ReadOnlyValue` thành lưới** như bản đầu (khách chê 04/09/2026): tám khung xám
 * xếp hàng đọc ra y hệt một cái form bị khoá, trong khi đây là thứ người duyệt
 * ĐỌC chứ không phải điền.
 *
 * Bố cục theo thứ tự câu hỏi của người duyệt: **họp gì → khi nào, ở đâu → ai dự
 * → chuẩn bị gì**. Ba con số quyết định (ngày · giờ · phòng) đứng thành một dải
 * lớn ở trên cùng; phần còn lại là chữ thường, và **ô rỗng thì không dựng** —
 * một khung xám trống rỗng chỉ tốn chỗ mà không nói gì.
 */
export function RoomBookingSummary({ booking }: { booking: RoomBooking }) {
  const attendees = booking.attendees ?? []
  const minutes = minutesBetween(booking.start_at, booking.end_at)
  const hours = Math.floor(minutes / 60)
  const restMinutes = minutes % 60

  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
          Nội dung cuộc họp
        </p>
        <p className="mt-1 text-xl font-semibold">{booking.title || '—'}</p>
      </div>

      {/*  Dải ba con số quyết định. Người duyệt nhìn đúng ba thứ này trước khi
           bấm: bao giờ · ở đâu · bao lâu. */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <Stat icon={CalendarDays} label="Ngày họp" value={formatDate(booking.start_at)} />
        <Stat
          icon={Clock}
          label="Khung giờ"
          value={formatTimeRange(booking.start_at, booking.end_at)}
          hint={`${hours ? `${hours} giờ` : ''}${restMinutes ? ` ${restMinutes} phút` : ''}`.trim()}
        />
        <Stat
          icon={DoorOpen}
          label="Phòng họp"
          value={booking.room_name || `#${booking.room_id}`}
          hint={booking.room_code}
        />
      </div>

      <dl className="grid grid-cols-1 gap-x-8 gap-y-4 sm:grid-cols-2">
        <Row label="Người đặt" value={booking.requester_name || '—'} />
        <Row
          label="Số người dự (dự kiến)"
          value={booking.attendee_count ? `${booking.attendee_count} người` : '—'}
        />
        {booking.purpose ? (
          <div className="sm:col-span-2">
            <Row label="Ghi chú / chuẩn bị" value={booking.purpose} multiline />
          </div>
        ) : null}
      </dl>

      {/*  ⚠️ Khối này LUÔN dựng, kể cả khi chưa mời ai — cùng lẽ với mục «Bàn
           giao công việc» của đơn nghỉ phép: người duyệt phải phân biệt được
           *"người đặt chưa mời ai"* với *"màn hình thiếu mục đó"*. Số người dự
           so với sức chứa phòng là thứ họ cân nhắc để bấm Duyệt hay Trả về. */}
      <div>
        <p className="flex items-center gap-1.5 text-xs font-medium tracking-wide text-muted-foreground uppercase">
          <Users className="size-3.5" />
          Mời tham dự
        </p>
        {attendees.length > 0 ? (
          <ul className="mt-2 flex flex-wrap gap-1.5">
            {attendees.map((a) => (
              <li
                key={a.id}
                className="rounded-full border bg-muted/40 px-2.5 py-1 text-sm"
              >
                {a.employee_name || `#${a.employee_id}`}
                {a.role ? <span className="text-muted-foreground"> · {a.role}</span> : null}
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-1.5 text-sm text-muted-foreground">
            Chưa mời ai đích danh — phiếu này chỉ giữ phòng.
          </p>
        )}
      </div>
    </div>
  )
}

function Stat({
  icon: Icon,
  label,
  value,
  hint,
}: {
  icon: typeof CalendarDays
  label: string
  value: string
  hint?: string
}) {
  return (
    <div className="rounded-lg border bg-muted/30 p-3">
      <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
        <Icon className="size-3.5" />
        {label}
      </p>
      <p className="mt-1 truncate font-semibold">{value}</p>
      {hint ? <p className="text-xs text-muted-foreground">{hint}</p> : null}
    </div>
  )
}

function Row({
  label,
  value,
  multiline = false,
}: {
  label: string
  value: string
  multiline?: boolean
}) {
  return (
    <div>
      <dt className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
        {label}
      </dt>
      <dd className={multiline ? 'mt-1 text-sm whitespace-pre-wrap' : 'mt-1 text-sm font-medium'}>
        {value}
      </dd>
    </div>
  )
}
