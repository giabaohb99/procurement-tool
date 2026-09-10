import { useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'
import {
  vehicleBookingTimelineApi,
  type TimelineParams,
} from '../api/vehicle-booking-timeline-api'

/**
 * Chuyến xe theo dòng thời gian cho lịch Timeline. Khoảng ngày (do FullCalendar
 * báo mỗi lần đổi tháng) nằm trong query-key nên tự nạp lại khi chuyển tháng;
 * `enabled` chờ có khoảng hợp lệ để không gọi khi lịch chưa dựng xong.
 */
export function useVehicleBookingTimeline(params: TimelineParams | null) {
  return useQuery({
    queryKey: queryKeys.vehicleBooking.timeline(
      params ? { date_from: params.date_from, date_to: params.date_to } : {},
    ),
    queryFn: () => vehicleBookingTimelineApi.getTimeline(params as TimelineParams),
    enabled: Boolean(params?.date_from && params?.date_to),
  })
}
