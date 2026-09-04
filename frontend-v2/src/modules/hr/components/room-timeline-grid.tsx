import { Plus, Users } from 'lucide-react'

import { cn } from '@/shared/utils/cn'
import { useTimelineDrag, type TimelineDrop } from '../hooks/use-timeline-drag'
import type { MeetingRoom, RoomBooking } from '../types/room'
import {
  buildRowBars,
  DAY_START_HOUR,
  dimBandsX,
  formatSlotHour,
  halfHourSlots,
  hourLabels,
  hourPercent,
  nowLineLeft,
  rowHeightFor,
} from '../utils/room-calendar-grid'
import { RoomBookingBar } from './room-booking-bar'

interface RoomTimelineGridProps {
  day: Date
  rooms: MeetingRoom[]
  bookings: RoomBooking[]
  onOpenBooking: (booking: RoomBooking) => void
  onPickSlot?: (roomId: number, hour: number) => void
  /**
   * Thả một khối xuống chỗ mới. Bỏ trống = **tắt kéo thả** (thiếu quyền sửa),
   * khối vẫn bấm mở phiếu như cũ.
   */
  onReschedule?: (booking: RoomBooking, roomId: number, start: string, end: string) => void
  /** Mốc «bây giờ». Truyền vào để bài kiểm không phụ thuộc đồng hồ máy. */
  now?: Date
}

/** Bề rộng cột tên phòng — dính bên trái khi cuộn ngang. */
const ROOM_COL = 200
/** Bề ngang tối thiểu của phần lưới giờ; hẹp hơn thì cuộn ngang. */
const GRID_MIN_WIDTH = 820

/** Vị trí + bề rộng của một khoảng giờ trên trục ngang, tính theo %. */
function barPercent(start: string, end: string) {
  const from = new Date(start)
  const to = new Date(end)
  const left = hourPercent(from.getHours() + from.getMinutes() / 60)
  const right = hourPercent(to.getHours() + to.getMinutes() / 60)
  return { leftPercent: left, widthPercent: Math.max(1, right - left) }
}

/**
 * LƯỚI MỘT NGÀY — **mỗi phòng một HÀNG**, giờ chạy ngang.
 *
 * ⚠️ Đảo trục từ bản «cột = phòng» vì khách hỏi đúng câu quyết định: *"20 phòng
 * thì sao?"* — 20 cột là 4.500px bề ngang, cuộn bốn màn hình mới xem hết. Đảo
 * trục thì số phòng chỉ làm lưới **dài xuống** (cuộn dọc, thao tác ai cũng làm
 * sẵn), còn cả ngày làm việc nằm trọn trong một màn.
 *
 * Hai thứ **co giãn**, và cả hai đều vì cùng một lời chê: bốn phòng mà lưới cao
 * 210px giữa khung rỗng 1.100px, lại chừa một nghìn pixel trắng bên phải.
 *
 * * **Trục giờ tính bằng phần trăm** → lưới luôn lấp đầy bề ngang khung; khung
 *   hẹp hơn `GRID_MIN_WIDTH` thì cuộn ngang.
 * * **Hàng cao theo số phòng** (`rowHeightFor`) → ít phòng thì hàng dày và khối
 *   phiếu đọc thoải mái; nhiều phòng thì hàng mỏng để lọt được nhiều dòng.
 *
 * **KÉO THẢ** (`onReschedule`): kéo ngang đổi giờ, kéo dọc đổi phòng, kéo mép
 * đổi độ dài — xem `useTimelineDrag` và `room-drag.ts`.
 */
export function RoomTimelineGrid({
  day,
  rooms,
  bookings,
  onOpenBooking,
  onPickSlot,
  onReschedule,
  now = new Date(),
}: RoomTimelineGridProps) {
  const labels = hourLabels()
  const slots = halfHourSlots()
  const bands = dimBandsX()
  const nowLeft = nowLineLeft(day, now)
  const rowHeight = rowHeightFor(rooms.length)

  const { drag, onPointerDown, onPointerMove, onPointerUp } = useTimelineDrag({
    day,
    rowHeight,
    roomCount: rooms.length,
    onClick: onOpenBooking,
    onDrop: (drop: TimelineDrop) => {
      const room = rooms[drop.roomIndex]
      onReschedule?.(drop.booking, room?.id ?? drop.booking.room_id, drop.start, drop.end)
    },
  })

  if (!rooms.length) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 p-10 text-center">
        <p className="text-sm font-medium">Không có phòng nào</p>
        <p className="max-w-sm text-sm text-muted-foreground">
          Bỏ bớt bộ lọc, hoặc vào tab «Danh mục phòng» để thêm phòng.
        </p>
      </div>
    )
  }

  return (
    <div className="min-h-0 overflow-auto">
      <div className="flex min-w-max flex-col">
        {/* Thước giờ — dính đỉnh khi cuộn dọc qua hai chục phòng. */}
        <div className="sticky top-0 z-30 flex border-b bg-muted/40">
          <div
            className="sticky left-0 z-40 shrink-0 border-r bg-muted/40 px-3 py-2 text-xs font-medium text-muted-foreground"
            style={{ width: ROOM_COL }}
          >
            Phòng
          </div>
          <div className="relative h-9 flex-1" style={{ minWidth: GRID_MIN_WIDTH }}>
            {labels.slice(0, -1).map((label) => (
              <div
                key={label}
                className="absolute top-0 h-9 border-l pt-2 pl-1.5 text-[11px] font-medium text-muted-foreground tabular-nums"
                style={{ left: `${hourPercent(Number(label.slice(0, 2)))}%` }}
              >
                {label}
              </div>
            ))}
            {nowLeft !== null && (
              <div
                className="absolute top-1.5 z-10 -translate-x-1/2 rounded bg-destructive px-1 py-0.5 text-[10px] font-semibold text-white tabular-nums"
                style={{ left: `${nowLeft}%` }}
              >
                {formatSlotHour(now.getHours() + now.getMinutes() / 60)}
              </div>
            )}
          </div>
        </div>

        {rooms.map((room, roomIndex) => {
          const bars = buildRowBars(
            bookings.filter((b) => b.room_id === room.id),
            day,
          )
          //  Bản XEM TRƯỚC vẽ ở hàng người dùng đang trỏ tới, không phải hàng gốc
          //  — kéo dọc để đổi phòng thì phải thấy nó rơi vào đúng phòng nào.
          const preview = drag?.moved && drag.roomIndex === roomIndex ? drag : null
          return (
            <div key={room.id} className="flex border-b last:border-b-0">
              {/* Tên phòng — dính bên trái khi cuộn ngang tới cuối ngày. */}
              <div
                className="sticky left-0 z-20 flex shrink-0 items-center justify-between gap-2 border-r bg-card px-3"
                style={{ width: ROOM_COL, height: rowHeight }}
              >
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium leading-tight">{room.name}</p>
                  {room.location ? (
                    <p className="truncate text-[11px] text-muted-foreground">{room.location}</p>
                  ) : null}
                </div>
                {room.capacity ? (
                  <span className="flex shrink-0 items-center gap-1 text-[11px] text-muted-foreground">
                    <Users className="size-3" />
                    {room.capacity}
                  </span>
                ) : null}
              </div>

              <div
                //  ⚠️ Mốc đo bề ngang của tầng kéo thả (`closest('[data-room-lane]')`).
                //  Bỏ thuộc tính này là mọi phép đổi pixel → phút ra 0.
                data-room-lane
                className="relative flex-1"
                style={{ height: rowHeight, minWidth: GRID_MIN_WIDTH }}
              >
                {bands.map((band) => (
                  <div
                    key={band.leftPercent}
                    className="pointer-events-none absolute inset-y-0 bg-muted/40"
                    style={{ left: `${band.leftPercent}%`, width: `${band.widthPercent}%` }}
                  />
                ))}

                {slots.map((hour) => {
                  const isHalf = hour % 1 !== 0
                  return (
                    <button
                      key={hour}
                      type="button"
                      className={cn(
                        'group absolute inset-y-0 flex items-center justify-center border-l transition-colors hover:bg-primary/10',
                        isHalf ? 'border-dashed border-border/40' : 'border-border/70',
                      )}
                      style={{
                        left: `${hourPercent(hour)}%`,
                        width: `${hourPercent(DAY_START_HOUR + 0.5)}%`,
                      }}
                      aria-label={`Đặt ${room.name} lúc ${formatSlotHour(hour)}`}
                      onClick={() => onPickSlot?.(room.id, hour)}
                    >
                      {/*  Nhãn hiện TRONG ô lúc rê chuột — thay cho `title`, vốn
                           là tooltip xám của trình duyệt, chờ một giây mới ra.
                           Nền NHẠT chứ không tô đặc màu chính: đây là gợi ý
                           "đặt được ở đây", không phải một nút hành động. */}
                      <span className="pointer-events-none flex items-center gap-0.5 rounded border border-primary/30 bg-primary/10 px-1.5 py-0.5 text-[10px] font-medium text-primary opacity-0 transition-opacity group-hover:opacity-100">
                        <Plus className="size-2.5" />
                        {formatSlotHour(hour)}
                      </span>
                    </button>
                  )
                })}

                {nowLeft !== null && (
                  <div
                    className="pointer-events-none absolute inset-y-0 z-10 border-l-2 border-destructive"
                    style={{ left: `${nowLeft}%` }}
                  />
                )}

                {bars.map((bar) => (
                  <RoomBookingBar
                    key={bar.booking.id}
                    booking={bar.booking}
                    leftPercent={bar.leftPercent}
                    widthPercent={bar.widthPercent}
                    topPercent={bar.topPercent}
                    heightPercent={bar.heightPercent}
                    rowHeight={rowHeight}
                    draggable={Boolean(onReschedule)}
                    dragging={drag?.bookingId === bar.booking.id && drag.moved}
                    onOpen={() => onOpenBooking(bar.booking)}
                    onDragStart={(event, mode) =>
                      onPointerDown(event, bar.booking, mode, roomIndex)
                    }
                    onDragMove={onPointerMove}
                    onDragEnd={onPointerUp}
                  />
                ))}

                {/*  XEM TRƯỚC: khung nét đứt + giờ mới, bám nam châm 15 phút.
                     Không có nó thì người dùng kéo mù — khối gốc đứng yên cho tới
                     lúc máy chủ trả lời, và họ không biết mình đang thả vào đâu. */}
                {preview && (
                  <div
                    className="pointer-events-none absolute z-20 flex items-center justify-center rounded border-2 border-dashed border-primary bg-primary/15 px-1"
                    style={{
                      top: 2,
                      height: rowHeight - 4,
                      left: `${barPercent(preview.range.start, preview.range.end).leftPercent}%`,
                      width: `${barPercent(preview.range.start, preview.range.end).widthPercent}%`,
                    }}
                  >
                    <span className="truncate text-[11px] font-semibold text-primary tabular-nums">
                      {preview.range.start.slice(11)} – {preview.range.end.slice(11)}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
