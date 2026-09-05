import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { appConfig } from '@/core/config/app-config'
import { queryKeys } from '@/shared/constants/query-keys'
import type { ListParams } from '@/shared/types/api'
import { dispatchOptionsApi, vehicleBookingApi } from '../api/vehicle-booking-api'
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

/** Điều phối: gán xe + tài xế cho phiếu. */
export function useDispatchVehicleBooking() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      id,
      assigned_vehicle_id,
      assigned_driver_id,
    }: {
      id: number
      assigned_vehicle_id: number
      assigned_driver_id: number
    }) => vehicleBookingApi.dispatch(id, { assigned_vehicle_id, assigned_driver_id }),
    onSuccess: (_data, { id }) => {
      qc.invalidateQueries({ queryKey: queryKeys.vehicleBooking.all })
      qc.invalidateQueries({ queryKey: queryKeys.vehicleBooking.booking(id) })
      toast.success('Đã điều phối xe & tài xế')
    },
  })
}

/** Danh sách Xe để đổ vào ô chọn khi điều phối (danh mục đổi thưa → giữ 5 phút). */
export function useVehicleOptions() {
  return useQuery({
    queryKey: ['vehicle-booking', 'vehicle-options'],
    queryFn: dispatchOptionsApi.vehicles,
    staleTime: 5 * 60 * 1000,
  })
}

/** Danh sách Tài xế để đổ vào ô chọn khi điều phối. */
export function useDriverOptions() {
  return useQuery({
    queryKey: ['vehicle-booking', 'driver-options'],
    queryFn: dispatchOptionsApi.drivers,
    staleTime: 5 * 60 * 1000,
  })
}

/** Hồ sơ tài xế của chính người đăng nhập — để form TỰ LÁI tự điền GPLX. */
export function useMyDriver(enabled = true) {
  return useQuery({
    queryKey: ['vehicle-booking', 'my-driver'],
    queryFn: dispatchOptionsApi.myDriver,
    staleTime: 5 * 60 * 1000,
    enabled,
  })
}

/**
 * Các nút chuyển trạng thái theo vai trò (duyệt / trả / từ chối · tài xế nhận /
 * bắt đầu / hoàn tất). Mọi mutation làm mới danh sách + chi tiết và bắn toast từ
 * thông điệp `message` server trả về — nên thông điệp chỉ khai một chỗ (backend).
 */
function useBookingTransition<TVars extends { id: number }>(
  mutationFn: (vars: TVars) => Promise<unknown>,
  successMsg: string,
) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn,
    onSuccess: (_data, { id }) => {
      qc.invalidateQueries({ queryKey: queryKeys.vehicleBooking.all })
      qc.invalidateQueries({ queryKey: queryKeys.vehicleBooking.booking(id) })
      toast.success(successMsg)
    },
  })
}

export function useApproveBooking() {
  return useBookingTransition(({ id }: { id: number }) => vehicleBookingApi.approve(id), 'Đã duyệt yêu cầu')
}
export function useReturnBooking() {
  return useBookingTransition(
    ({ id, reason }: { id: number; reason: string }) => vehicleBookingApi.returnForEdit(id, reason),
    'Đã trả lại để chỉnh sửa',
  )
}
export function useRejectBooking() {
  return useBookingTransition(
    ({ id, reason }: { id: number; reason: string }) => vehicleBookingApi.reject(id, reason),
    'Đã từ chối yêu cầu',
  )
}
export function useDriverAcceptBooking() {
  return useBookingTransition(
    ({ id }: { id: number }) => vehicleBookingApi.driverAccept(id),
    'Đã nhận chuyến',
  )
}
export function useDriverRejectBooking() {
  return useBookingTransition(
    ({ id, reason }: { id: number; reason: string }) => vehicleBookingApi.driverReject(id, reason),
    'Đã từ chối chuyến — chờ điều phối lại',
  )
}
export function useDriverStartBooking() {
  return useBookingTransition(
    ({ id }: { id: number }) => vehicleBookingApi.driverStart(id),
    'Đã bắt đầu chuyến',
  )
}
export function useDriverCompleteBooking() {
  return useBookingTransition(
    ({ id, distance_km, cost }: { id: number; distance_km?: number; cost?: number }) =>
      vehicleBookingApi.driverComplete(id, { distance_km, cost }),
    'Đã hoàn tất chuyến',
  )
}

/** Sửa phiếu (chỉ khi còn nháp / bị trả về) — `submit` để gửi duyệt sau khi lưu. */
export function useUpdateVehicleBooking() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      id,
      payload,
      submit,
    }: {
      id: number
      payload: Partial<VehicleBookingPayload>
      submit: boolean
    }) => vehicleBookingApi.update(id, payload, submit),
    onSuccess: (_data, { id, submit }) => {
      qc.invalidateQueries({ queryKey: queryKeys.vehicleBooking.all })
      qc.invalidateQueries({ queryKey: queryKeys.vehicleBooking.booking(id) })
      toast.success(submit ? 'Đã gửi duyệt yêu cầu đặt xe' : 'Đã lưu thay đổi')
    },
  })
}
