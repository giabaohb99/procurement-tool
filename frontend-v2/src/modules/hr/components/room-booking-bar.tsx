import { cn } from '@/shared/utils/cn'
import { ROOM_BOOKING_STATUS, type RoomBooking } from '../types/room'
import type { DragMode } from '../utils/room-drag'
import { formatTimeRange } from '../utils/room-time'

interface RoomBookingBarProps {
  booking: RoomBooking
  leftPercent: number
  widthPercent: number
  topPercent: number
  heightPercent: number
  /** Chiều cao hàng (px) — quyết định có đủ chỗ ghi tên người đặt không. */
  rowHeight: number
  /** Kéo thả được không. Tắt thì khối vẫn bấm mở phiếu như cũ. */
  draggable: boolean
  /** Đang được kéo — khối gốc mờ đi, bản xem trước vẽ ở chỗ mới. */
  dragging: boolean
  onOpen: () => void
  onDragStart: (event: React.PointerEvent, mode: DragMode) => void
  onDragMove: (event: React.PointerEvent) => void
  onDragEnd: (event: React.PointerEvent) => void
}

/**
 * MỘT KHỐI PHIẾU trên lưới lịch.
 *
 * Khối **tô đặc, chữ trắng, bo 4px, không viền không đổ bóng** — đúng lối lịch
 * quen tay (Google Calendar). Hai bản trước đều hỏng vì hai lý do ngược nhau:
 * nền trắng viền mảnh thì tàng hình trên lưới trắng, còn nền tô nhạt + viền +
 * dải trái + đổ bóng thì mỗi khối gánh bốn thứ trang trí, nhìn ra "thẻ" chứ
 * không ra "lịch". Màu là thứ DUY NHẤT phân biệt trạng thái.
 */
export function RoomBookingBar({
  booking,
  leftPercent,
  widthPercent,
  topPercent,
  heightPercent,
  rowHeight,
  draggable,
  dragging,
  onOpen,
  onDragStart,
  onDragMove,
  onDragEnd,
}: RoomBookingBarProps) {
  const isApproved = booking.status === ROOM_BOOKING_STATUS.APPROVED
  //  Khối HẸP (họp 30 phút) hoặc THẤP (hai phiếu chồng giờ chia đôi hàng) chỉ đủ
  //  chỗ cho MỘT dòng — nhồi thêm dòng giờ thì hai dòng chữ đè lên nhau.
  //  Điều kiện đi theo BỀ RỘNG, KHÔNG theo chiều cao hàng: hàng 48px vẫn thừa
  //  chỗ cho hai dòng 11px, mà 48px lại đúng là cỡ hàng của công ty nhiều phòng
  //  — buộc theo chiều cao thì số đông người dùng không bao giờ thấy giờ.
  const isTight = heightPercent < 100 || widthPercent < 7

  return (
    <div
      className="absolute z-10 flex"
      /*  Chừa 1px quanh khối để hai phiếu liền giờ không dính thành một vệt. */
      style={{
        left: `calc(${leftPercent}% + 1px)`,
        width: `calc(${widthPercent}% - 2px)`,
        top: `calc(${topPercent}% + 1px)`,
        height: `calc(${heightPercent}% - 2px)`,
      }}
    >
      <button
        type="button"
        /*  ⚠️ KHÔNG dùng `onClick`. Kéo và bấm đi chung một nút, nên việc "đây là
            cú bấm hay cú kéo" do `useTimelineDrag` phân xử ở lúc nhả chuột —
            gắn thêm `onClick` là kéo xong bị mở luôn trang chi tiết. */
        onPointerDown={draggable ? (event) => onDragStart(event, 'move') : undefined}
        onPointerMove={draggable ? onDragMove : undefined}
        onPointerUp={draggable ? onDragEnd : undefined}
        //  Không kéo được thì quay về cú bấm thường — bàn phím vẫn mở được phiếu.
        onClick={draggable ? undefined : onOpen}
        className={cn(
          'flex min-w-0 flex-1 flex-col justify-center overflow-hidden rounded px-1.5 text-left leading-tight text-white transition-colors hover:z-20',
          draggable ? 'cursor-grab active:cursor-grabbing' : 'cursor-pointer',
          dragging && 'opacity-40',
          isApproved
            ? 'bg-emerald-600 hover:bg-emerald-700'
            //  Chờ duyệt vẫn GIỮ phòng nên tô đặc y như đã duyệt, chỉ khác sắc
            //  để biết nó còn có thể bị trả về.
            : 'bg-amber-500 hover:bg-amber-600',
        )}
        title={
          `${booking.code} · ${booking.title} · ` +
          `${formatTimeRange(booking.start_at, booking.end_at)} · ${booking.requester_name}` +
          (draggable ? ' — kéo để dời giờ, kéo mép để đổi độ dài' : '')
        }
      >
        <span className="truncate text-xs font-medium">{booking.title}</span>
        {!isTight && (
          <span className="truncate text-[11px] text-white/85 tabular-nums">
            {formatTimeRange(booking.start_at, booking.end_at)}
            {rowHeight >= 84 && booking.requester_name ? ` · ${booking.requester_name}` : ''}
          </span>
        )}
      </button>

      {/*  TAY NẮM hai mép — chỉ 6px và trong suốt, chỉ đổi con trỏ khi rê tới.
           Vẽ thành vạch nhìn thấy được thì mỗi khối mọc thêm hai chi tiết, mà
           lưới hai chục phòng đã đủ đông rồi. */}
      {draggable && (
        <>
          <span
            role="presentation"
            className="absolute inset-y-0 left-0 w-1.5 cursor-ew-resize"
            onPointerDown={(event) => onDragStart(event, 'resize-start')}
            onPointerMove={onDragMove}
            onPointerUp={onDragEnd}
          />
          <span
            role="presentation"
            className="absolute inset-y-0 right-0 w-1.5 cursor-ew-resize"
            onPointerDown={(event) => onDragStart(event, 'resize-end')}
            onPointerMove={onDragMove}
            onPointerUp={onDragEnd}
          />
        </>
      )}
    </div>
  )
}
