import { useMemo } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { ROOM_BOOKING_STATUS, type RoomBooking } from '../types/room'
import { useRoomBookings } from './use-room'

export interface RoomGlance {
  /** Phiếu ĐÃ DUYỆT có giờ họp giao với hôm nay, xếp theo giờ bắt đầu. */
  today: RoomBooking[]
  /** Phiếu đang chờ duyệt trong phạm vi người xem. */
  pending: number
  canRead: boolean
  isLoading: boolean
}

/**
 * "Hôm nay phòng nào bận" — câu hỏi hằng ngày của phân hệ Đặt phòng họp.
 *
 * Cùng khuôn `use-hr-leave-glance.ts`: đi qua `room_booking.read` nên kết quả
 * ĐÃ THEO PHẠM VI người xem, không có con số toàn công ty nào lọt ra.
 */
export function useHrRoomGlance(): RoomGlance {
  const { can } = usePermission()
  const canRead = can('room_booking', 'read')

  const { from, to } = todayBounds(new Date())

  //  `from_time`/`to_time` lọc theo GIAO NHAU của khoảng, nên cuộc họp bắt đầu
  //  từ hôm qua kéo sang sáng nay vẫn lọt vào — xem docstring `list_bookings`.
  //
  //  ⚠️ Chuỗi giờ ghép TAY theo giờ ĐỊA PHƯƠNG, tuyệt đối không `toISOString()`:
  //  backend khai kiểu `LocalDateTime` (từ chối chuỗi có múi giờ), và máy chạy ở
  //  UTC+7 nên `toISOString` lùi 7 tiếng — mốc 00:00 hôm nay thành 17:00 hôm qua
  //  và thẻ đổ ra lịch họp của ngày hôm trước.
  const todayQuery = useRoomBookings(
    {
      page: 1,
      page_size: 50,
      status: ROOM_BOOKING_STATUS.APPROVED,
      from_time: from,
      to_time: to,
      sort_by: 'start_at',
      sort_dir: 'asc',
    },
    canRead,
  )

  //  `page_size: 1` — chỉ cần `total`.
  const pendingQuery = useRoomBookings(
    { page: 1, page_size: 1, status: ROOM_BOOKING_STATUS.PENDING },
    canRead,
  )

  const today = useMemo(() => todayQuery.data?.items ?? [], [todayQuery.data])

  return {
    today,
    pending: pendingQuery.data?.total ?? 0,
    canRead,
    isLoading: canRead && todayQuery.isPending,
  }
}

/** Hai đầu mút của ngày hôm nay, dạng `YYYY-MM-DDTHH:MM:SS` giờ địa phương. */
function todayBounds(now: Date): { from: string; to: string } {
  const day = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`
  return { from: `${day}T00:00:00`, to: `${day}T23:59:59` }
}

function pad(value: number): string {
  return String(value).padStart(2, '0')
}
