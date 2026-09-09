import { useMemo } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { toDateInputValue } from '@/shared/utils/format-date'
import { LEAVE_STATUS, type LeaveRequest } from '../types/leave'
import { useLeaveRequests } from './use-leave'

/** Số ngày nhìn tới của khối "Nghỉ phép sắp tới". */
export const LEAVE_GLANCE_DAYS = 7

export interface LeaveGlance {
  /** Đơn đang chờ duyệt trong phạm vi người xem. */
  pending: number
  /** Đơn ĐÃ DUYỆT có ngày nghỉ giao với [hôm nay, hôm nay + `LEAVE_GLANCE_DAYS`]. */
  upcoming: LeaveRequest[]
  /** Trong số đó, bao nhiêu đơn phủ đúng ngày hôm nay. */
  offToday: number
  /** `YYYY-MM-DD` của hôm nay — thẻ dùng để đánh dấu dòng "đang nghỉ". */
  today: string
  canRead: boolean
  isLoading: boolean
  isLoadingPending: boolean
}

/**
 * Hai con số nghỉ phép đủ để mở đầu ngày làm việc: hôm nay ai vắng, và còn bao
 * nhiêu đơn treo trên bàn mình.
 *
 * Cả hai đi qua `leave_request.read` nên KẾT QUẢ ĐÃ THEO PHẠM VI của người xem:
 * nhân viên thường chỉ thấy đơn của chính mình, trưởng phòng thấy cả phòng. Đó
 * là chủ ý — không có con số "toàn công ty" nào lọt ra ở đây.
 */
export function useHrLeaveGlance(): LeaveGlance {
  const { can } = usePermission()
  const canRead = can('leave_request', 'read')

  const today = toDateInputValue(new Date())
  const until = toDateInputValue(addDays(new Date(), LEAVE_GLANCE_DAYS))

  //  `page_size: 1` — chỉ cần `total`, không kéo bản ghi nào về.
  const pendingQuery = useLeaveRequests(
    { page: 1, page_size: 1, status: LEAVE_STATUS.PENDING },
    { enabled: canRead },
  )

  //  `from_date`/`to_date` của endpoint này lọc theo GIAO NHAU của khoảng, nên
  //  đơn bắt đầu từ tuần trước mà còn kéo sang hôm nay vẫn lọt vào — xem
  //  docstring `list_requests` ở backend.
  const upcomingQuery = useLeaveRequests(
    {
      page: 1,
      page_size: 50,
      status: LEAVE_STATUS.APPROVED,
      from_date: today,
      to_date: until,
      sort_by: 'from_date',
      sort_dir: 'asc',
    },
    { enabled: canRead },
  )

  const upcoming = useMemo(() => upcomingQuery.data?.items ?? [], [upcomingQuery.data])

  //  So sánh CHUỖI `YYYY-MM-DD` thay vì dựng `Date`: dạng này so theo thứ tự từ
  //  điển là ra đúng thứ tự thời gian, và không dính chuyện chuỗi ngày trần bị
  //  hiểu là mốc UTC rồi lùi mất một ngày ở múi giờ dương.
  const offToday = upcoming.filter(
    (request) => request.from_date <= today && request.to_date >= today,
  ).length

  return {
    pending: pendingQuery.data?.total ?? 0,
    upcoming,
    offToday,
    today,
    canRead,
    isLoading: canRead && upcomingQuery.isPending,
    isLoadingPending: canRead && pendingQuery.isPending,
  }
}

function addDays(date: Date, days: number): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate() + days)
}
