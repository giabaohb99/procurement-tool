import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { appConfig } from '@/core/config/app-config'
import { queryKeys } from '@/shared/constants/query-keys'
import type { ListParams } from '@/shared/types/api'
import { vehicleBookingApi } from '../api/vehicle-booking-api'
import type { VehicleBookingPayload } from '../types/vehicle-booking'

/** Danh sách phiếu đặt xe trong phạm vi người xem. Server phân trang. */
export function useVehicleBookings(params: ListParams = {}) {
  const query: ListParams = {
    page: 1,
    page_size: appConfig.defaultPageSize,
    ...params,
  }
  return useQuery({
    queryKey: queryKeys.vehicleBooking.bookings(query),
    queryFn: () => vehicleBookingApi.list(query),
    placeholderData: keepPreviousData,
  })
}

export function useVehicleBooking(id: number | null) {
  return useQuery({
    queryKey: queryKeys.vehicleBooking.booking(id ?? 0),
    queryFn: () => vehicleBookingApi.get(id as number),
    enabled: id !== null && id > 0,
  })
}

/** Tạo phiếu — `submit` quyết định lưu nháp hay gửi duyệt. */
export function useCreateVehicleBooking() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ payload, submit }: { payload: VehicleBookingPayload; submit: boolean }) =>
      vehicleBookingApi.create(payload, submit),
    onSuccess: (_data, { submit }) => {
      qc.invalidateQueries({ queryKey: queryKeys.vehicleBooking.all })
      toast.success(submit ? 'Đã gửi duyệt yêu cầu đặt xe' : 'Đã lưu nháp yêu cầu đặt xe')
    },
  })
}
