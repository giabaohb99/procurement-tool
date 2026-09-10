import { useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'
import {
  vehicleBookingDashboardApi,
  type BookingOverviewParams,
} from '../api/vehicle-booking-dashboard-api'

/**
 * Số liệu trang Tổng quan Đặt xe. Một lần gọi cho cả trang — backend gom sẵn các
 * khối theo vai trò. `params` (khoảng ngày) chỉ đổi khối tổng hợp; nằm trong
 * query-key để tự nạp lại khi đổi.
 */
export function useVehicleBookingDashboard(params?: BookingOverviewParams) {
  return useQuery({
    queryKey: queryKeys.vehicleBooking.overview({
      date_from: params?.date_from ?? '',
      date_to: params?.date_to ?? '',
    }),
    queryFn: () => vehicleBookingDashboardApi.getOverview(params),
  })
}
