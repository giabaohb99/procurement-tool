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
}
