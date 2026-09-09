import { Plus, Users } from 'lucide-react'

import { cn } from '@/shared/utils/cn'
import { ROOM_BOOKING_STATUS, type MeetingRoom, type RoomBooking } from '../types/room'
import { blockingOnly } from '../utils/room-calendar-grid'
import { formatTimeRange } from '../utils/room-time'
import { RoomStatusBadge } from './room-status-badge'

interface RoomDayListProps {
  rooms: MeetingRoom[]
  bookings: RoomBooking[]
  onOpenBooking: (booking: RoomBooking) => void
  /** Đặt phòng này (không kèm giờ). Bỏ trống = thiếu quyền tạo phiếu. */
  onPickRoom?: (roomId: number) => void
}

/**
 * LỊCH MỘT NGÀY Ở KHỔ HẸP — **danh sách phòng**, không phải lưới giờ.
 *
 * ⚠️ **Vì sao không co lưới lại cho vừa mà phải đổi hẳn hình dạng.** Lưới ngang
 * khai cột tên phòng cứng 200px và bề ngang tối thiểu 820px cho trục giờ. Trên
 * máy 390px, phần nhìn thấy được của trục giờ chỉ còn ~158px — **19% của một
 * ngày làm việc** — nên câu hỏi *"chiều nay phòng nào trống"* phải trả lời bằng
 * cách kéo ngang qua bốn màn hình. Bóp cột tên hay thu giờ lại đều không cứu
 * được: 13 tiếng × nửa tiếng một ô thì mỗi ô còn 6px, không bấm trúng.
 *
 * ⚠️ **CHIA HAI PHẦN: đang có lịch · còn trống.** Bản đầu đổ tất cả vào một
 * danh sách phẳng, và ngày chưa ai đặt gì thì màn hình thành **21 dòng giống
 * hệt nhau cùng nói một câu «Trống cả ngày»** — người dùng cuộn hết hai chục
 * dòng để biết một điều đáng ra nói bằng một câu (khách báo 09/09/2026). Nay:
 *
 * * **Phòng đang có lịch** đứng trên, mỗi phòng một khối đủ giờ giấc — đây là
 *   thứ trả lời câu hỏi của người vào xem lịch.
 * * **Phòng còn trống** gom xuống dưới thành **lưới hai cột**, mỗi phòng một ô
 *   nhỏ. Nó không còn là "tin tức" mà là một **danh sách để CHỌN**: người ta
 *   xuống đây khi muốn đặt, và lúc đó cái cần là thấy nhiều phòng cùng lúc với
 *   sức chứa của chúng, chứ không phải đọc lại hai chục lần chữ "trống".
 *
 * Nhờ vậy 18 phòng trống chiếm ~430px thay vì ~1.300px.
 *
 * ⚠️ **Không lồng nút trong nút.** Ô phòng trống là một `<button>`, từng phiếu
 * cũng là một `<button>` riêng — không cái nào nằm trong cái nào.
 */
export function RoomDayList({
  rooms,
  bookings,
  onOpenBooking,
  onPickRoom,
}: RoomDayListProps) {
  //  Chỉ phiếu ĐANG GIỮ phòng, cùng luật với lưới và với con số «lượt giữ» trên
  //  thanh công cụ — ba chỗ đếm khác nhau là ba con số khác nhau.
  const held = blockingOnly(bookings)

  const busy = rooms
    .map((room) => ({
      room,
      rows: held
        .filter((b) => b.room_id === room.id)
        .sort((a, b) => a.start_at.localeCompare(b.start_at)),
    }))
    .filter((entry) => entry.rows.length > 0)

  const free = rooms.filter((room) => !held.some((b) => b.room_id === room.id))

  return (
    <div className="min-h-0 divide-y overflow-y-auto">
      {busy.length > 0 && (
        <section>
          <SectionHeading text={`Đang có lịch · ${busy.length} phòng`} />
          <div className="divide-y">
            {busy.map(({ room, rows }) => (
              <div key={room.id} className="px-3 py-2.5">
                <div className="flex w-full items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{room.name}</p>
                    {room.location ? (
                      <p className="truncate text-xs text-muted-foreground">{room.location}</p>
                    ) : null}
                  </div>
                  <Capacity value={room.capacity} />
                </div>

                <ul className="mt-2 space-y-1.5">
                  {rows.map((booking) => (
                    <li key={booking.id}>
                      <button
                        type="button"
                        onClick={() => onOpenBooking(booking)}
                        className={cn(
                          //  Vạch màu bên trái + huy hiệu chữ, cố ý cả hai: vạch
                          //  để quét mắt qua cả danh sách, chữ để không phải đi
                          //  tra bảng chú giải. Chú giải màu vì thế BỎ HẲN ở khổ
                          //  hẹp — nó chiếm một hàng của thanh công cụ để giải
                          //  nghĩa thứ ngay bên dưới đã tự nói ra bằng lời.
                          'flex w-full items-center gap-2 rounded-md border border-l-4 bg-card px-2 py-1.5 text-left transition-colors active:bg-row-hover',
                          booking.status === ROOM_BOOKING_STATUS.APPROVED
                            ? 'border-l-emerald-500'
                            : 'border-l-amber-500',
                        )}
                      >
                        <span className="shrink-0 text-xs font-medium tabular-nums">
                          {formatTimeRange(booking.start_at, booking.end_at)}
                        </span>
                        <span className="min-w-0 flex-1 truncate text-sm">
                          {booking.title || booking.code}
                        </span>
                        <RoomStatusBadge
                          status={booking.status}
                          label={booking.status_label}
                          className="shrink-0 px-1.5 text-[10px]"
                        />
                      </button>
                    </li>
                  ))}

                  {onPickRoom && (
                    <li>
                      <button
                        type="button"
                        onClick={() => onPickRoom(room.id)}
                        className="flex items-center gap-1 text-xs font-medium text-primary"
                      >
                        <Plus className="size-3" />
                        Đặt thêm giờ khác
                      </button>
                    </li>
                  )}
                </ul>
              </div>
            ))}
          </div>
        </section>
      )}

      {free.length > 0 && (
        <section>
          <SectionHeading
            //  Cả ngày chưa ai đặt gì thì nói THẲNG ra bằng một câu, đừng để
            //  người dùng suy ra từ hai chục dòng giống nhau.
            text={
              busy.length === 0
                ? `Cả ${free.length} phòng đều trống hôm nay`
                : `Còn trống cả ngày · ${free.length} phòng`
            }
            hint={onPickRoom ? 'Chạm một phòng để đặt.' : undefined}
          />
          <div className="grid grid-cols-2 gap-2 px-3 pt-1 pb-3">
            {free.map((room) => (
              <button
                key={room.id}
                type="button"
                className="flex min-w-0 items-start justify-between gap-1.5 rounded-md border px-2 py-1.5 text-left transition-colors active:bg-row-hover disabled:opacity-100"
                aria-label={onPickRoom ? `Đặt ${room.name}` : room.name}
                onClick={() => onPickRoom?.(room.id)}
                disabled={!onPickRoom}
              >
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{room.name}</p>
                  {room.location ? (
                    <p className="truncate text-xs text-muted-foreground">{room.location}</p>
                  ) : null}
                </div>
                <Capacity value={room.capacity} />
              </button>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}

/**
 * Tiêu đề một phần — dính đỉnh để biết đang cuộn trong phần nào.
 *
 * ⚠️ Nền phải ĐỤC (`bg-muted`, không phải `bg-muted/40`): dải dính mà trong suốt
 * thì tên phòng ở dưới trồi lên chồng chữ vào tiêu đề, đọc ra thành hai dòng đè
 * nhau — nhìn như lỗi hiển thị chứ không ra một dải tiêu đề.
 */
function SectionHeading({ text, hint }: { text: string; hint?: string }) {
  return (
    <div className="sticky top-0 z-10 border-b bg-muted px-3 py-1.5">
      <p className="text-xs font-semibold">{text}</p>
      {hint ? <p className="text-[11px] text-muted-foreground">{hint}</p> : null}
    </div>
  )
}

function Capacity({ value }: { value: number }) {
  if (!value) return null
  return (
    <span className="flex shrink-0 items-center gap-1 text-xs text-muted-foreground">
      <Users className="size-3" />
      {value}
    </span>
  )
}
