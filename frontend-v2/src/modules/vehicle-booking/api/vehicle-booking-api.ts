import { apiDelete, apiGet, apiPatch, apiPost } from '@/core/api'
import type { ListParams, PaginatedResult } from '@/shared/types/api'
import type { VehicleBooking, VehicleBookingPayload } from '../types/vehicle-booking'

const BASE_URL = '/api/vehicle-bookings'

export const vehicleBookingApi = {
  list: (params: ListParams) =>
    apiGet<PaginatedResult<VehicleBooking>>(BASE_URL, { params }),

  get: (id: number) => apiGet<VehicleBooking>(`${BASE_URL}/${id}`),

  /** `submit=true` gửi duyệt luôn; ngược lại lưu nháp. */
  create: (payload: VehicleBookingPayload, submit: boolean) =>
    apiPost<VehicleBooking>(BASE_URL, payload, { params: { submit } }),

  update: (id: number, payload: Partial<VehicleBookingPayload>, submit: boolean) =>
    apiPatch<VehicleBooking>(`${BASE_URL}/${id}`, payload, { params: { submit } }),

  remove: (id: number) => apiDelete<null>(`${BASE_URL}/${id}`),

  /** Điều phối: gán 1 xe + 1 tài xế cho phiếu. */
  dispatch: (id: number, payload: { assigned_vehicle_id: number; assigned_driver_id: number }) =>
    apiPost<VehicleBooking>(`${BASE_URL}/${id}/dispatch`, payload),
}

/** Xe/Tài xế đủ dùng để đổ vào ô chọn khi điều phối. */
export interface VehicleOption {
  id: number
  license_plate: string
  model: string
  status: string
  is_external: boolean
}
export interface DriverOption {
  id: number
  name: string
  phone: string
  status: string
  is_external: boolean
}

export const dispatchOptionsApi = {
  vehicles: () =>
    apiGet<PaginatedResult<VehicleOption>>('/api/vehicles', { params: { page_size: 500 } }),
  drivers: () =>
    apiGet<PaginatedResult<DriverOption>>('/api/drivers', { params: { page_size: 500 } }),
}
