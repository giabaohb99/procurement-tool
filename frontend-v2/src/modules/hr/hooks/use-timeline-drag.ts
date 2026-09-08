import { useCallback, useEffect, useRef, useState } from 'react'

import type { RoomBooking } from '../types/room'
import {
  clampRoomIndex,
  clampToGrid,
  draggedRange,
  isRealDrag,
  minutesFromDeltaX,
  type DragMode,
  type DraggedRange,
} from '../utils/room-drag'

export interface TimelineDrop extends DraggedRange {
  booking: RoomBooking
  /** Hàng phòng người dùng thả vào — có thể khác phòng ban đầu. */
  roomIndex: number
}

export interface TimelineDragState {
  bookingId: number
  mode: DragMode
  roomIndex: number
  range: DraggedRange
  /** Đã vượt ngưỡng rung tay chưa — dưới ngưỡng thì đây vẫn là một cú BẤM. */
  moved: boolean
}

interface Options {
  /** Ngày đang xem — mốc kẹp của lưới. Xem `clampToGrid`. */
  day: Date
  /** Chiều cao một hàng phòng (px) — dùng để đổi quãng kéo dọc thành số hàng. */
  rowHeight: number
  roomCount: number
  onDrop: (drop: TimelineDrop) => void
  onClick: (booking: RoomBooking) => void
}

/**
 * KÉO THẢ khối phiếu trên lưới lịch — bắt con trỏ, đổi ra giờ mới.
 *
 * Dùng **Pointer Events** chứ không phải HTML5 drag-and-drop: `draggable` gắn
 * kèm một ảnh ma của trình duyệt không tắt được, không chạy trên cảm ứng, và
 * không cho vẽ xem trước theo nam châm 15 phút. Bắt con trỏ
 * (`setPointerCapture`) thì kéo ra ngoài khối, ra ngoài cửa sổ, hay thả chuột ở
 * đâu cũng vẫn nhận được sự kiện.
 *
 * ⚠️ **Kéo và BẤM đi chung một nút.** Người ta bấm vào khối để mở phiếu, và
 * cũng chính khối đó kéo được. Phân biệt bằng quãng di chuyển (`isRealDrag`):
 * dưới ngưỡng thì gọi `onClick`, trên ngưỡng thì gọi `onDrop`. Nếu để `onClick`
 * nằm ở `onClick` của nút thì mỗi lần kéo xong người dùng bị mở luôn trang chi
 * tiết — kéo thả thành ra không dùng được.
 */
export function useTimelineDrag({ day, rowHeight, roomCount, onDrop, onClick }: Options) {
  const [drag, setDrag] = useState<TimelineDragState | null>(null)

  //  Giữ trong ref: các hàm xử lý sự kiện được gắn một lần, đọc `drag` từ state
  //  thì chúng bắt phải bản chụp cũ (giá trị lúc gắn) và mọi phép tính lệch.
  const session = useRef<{
    booking: RoomBooking
    mode: DragMode
    startX: number
    startY: number
    startRoomIndex: number
  } | null>(null)

  /**
   * Kết quả MỚI NHẤT của lượt kéo — nguồn duy nhất mà lúc thả chuột đọc.
   *
   * ⚠️ **Không được đọc `drag` (state) ở `onPointerUp`.** `setDrag` là bất đồng
   * bộ: kéo nhanh — một cú hất tay — thì `pointerup` tới ngay trong khung hình
   * của `pointermove` cuối, lúc đó React chưa vẽ lại và biến `drag` mà hàm nhìn
   * thấy vẫn là bản của lượt vẽ trước. Đo được 04/09/2026: hất tay 12 lần liên
   * tiếp thì **không lệnh ghi nào được gửi** — khối bật về chỗ cũ, người dùng
   * kéo mãi mà không có gì xảy ra. Kéo chậm thì lại lưu NHẦM sang giờ của lượt
   * vẽ trước, tệ hơn nữa vì nó im lặng.
   */
  const latest = useRef<{ roomIndex: number; range: DraggedRange } | null>(null)

  const finish = useCallback(() => {
    session.current = null
    latest.current = null
    setDrag(null)
  }, [])

  const onPointerDown = useCallback(
    (event: React.PointerEvent, booking: RoomBooking, mode: DragMode, roomIndex: number) => {
      //  Chuột phải / chuột giữa không kéo — để dành cho menu ngữ cảnh.
      if (event.button !== 0) return
      event.preventDefault()
      event.currentTarget.setPointerCapture?.(event.pointerId)
      session.current = {
        booking,
        mode,
        startX: event.clientX,
        startY: event.clientY,
        startRoomIndex: roomIndex,
      }
      setDrag({
        bookingId: booking.id,
        mode,
        roomIndex,
        range: { start: booking.start_at.slice(0, 16), end: booking.end_at.slice(0, 16) },
        moved: false,
      })
    },
    [],
  )

  const onPointerMove = useCallback(
    (event: React.PointerEvent) => {
      const active = session.current
      if (!active) return
      const deltaX = event.clientX - active.startX
      const deltaY = event.clientY - active.startY
      const moved = isRealDrag(deltaX, deltaY)

      //  Bề ngang THẬT của hàng đang kéo. Trục giờ tính theo phần trăm nên không
      //  có hằng số pixel nào để mượn — phải đo chính phần tử đó.
      const lane = (event.currentTarget as HTMLElement).closest('[data-room-lane]')
      const laneWidth = lane instanceof HTMLElement ? lane.clientWidth : 0
      const deltaMinutes = minutesFromDeltaX(deltaX, laneWidth)

      //  Kéo dọc chỉ có nghĩa khi dời CẢ khối; kéo mép mà đổi phòng thì một thao
      //  tác làm hai việc và người dùng không rút lại được nửa nào.
      const roomIndex =
        active.mode === 'move'
          ? clampRoomIndex(active.startRoomIndex + Math.round(deltaY / rowHeight), roomCount)
          : active.startRoomIndex

      const raw = draggedRange(
        active.booking.start_at,
        active.booking.end_at,
        active.mode,
        deltaMinutes,
      )
      //  KẸP vào khung lưới. Không kẹp thì kéo quá mép phải là phiếu lưu ở
      //  21:00 rồi biến mất khỏi lưới (lưới chỉ vẽ 7:00–20:00) — người dùng
      //  tưởng mình vừa xóa mất nó. `null` = không nhét vừa, giữ nguyên bản cũ.
      const range = clampToGrid(raw, active.mode, day)
      if (!range) return

      latest.current = { roomIndex, range }
      setDrag({ bookingId: active.booking.id, mode: active.mode, roomIndex, range, moved })
    },
    [day, rowHeight, roomCount],
  )

  const onPointerUp = useCallback(
    (event: React.PointerEvent) => {
      const active = session.current
      if (!active) return
      const deltaX = event.clientX - active.startX
      const deltaY = event.clientY - active.startY

      if (!isRealDrag(deltaX, deltaY)) {
        finish()
        onClick(active.booking)
        return
      }

      const current = latest.current
      finish()
      if (!current) return
      //  Thả về đúng chỗ cũ thì không gửi gì cả — một lệnh ghi "đổi từ 9:00
      //  sang 9:00" vẫn để lại một dòng dấu vết và một thư báo người dự.
      const unchanged =
        current.range.start === active.booking.start_at.slice(0, 16) &&
        current.range.end === active.booking.end_at.slice(0, 16) &&
        current.roomIndex === active.startRoomIndex
      if (unchanged) return
      onDrop({ booking: active.booking, roomIndex: current.roomIndex, ...current.range })
    },
    //  Cố ý KHÔNG phụ thuộc `drag`: hàm này đọc `latest.current`, và gắn `drag`
    //  vào đây là dựng lại hàm ở mọi khung hình của lượt kéo mà chẳng để làm gì.
    [finish, onClick, onDrop],
  )

  //  Thả chuột ngoài cửa sổ, hoặc trình duyệt hủy thao tác (cuộn bằng cảm ứng,
  //  Esc) thì phải dọn — không dọn là khối kẹt ở trạng thái đang kéo vĩnh viễn.
  useEffect(() => {
    if (!drag) return
    const cancel = () => finish()
    window.addEventListener('pointercancel', cancel)
    window.addEventListener('blur', cancel)
    return () => {
      window.removeEventListener('pointercancel', cancel)
      window.removeEventListener('blur', cancel)
    }
  }, [drag, finish])

  return { drag, onPointerDown, onPointerMove, onPointerUp }
}
