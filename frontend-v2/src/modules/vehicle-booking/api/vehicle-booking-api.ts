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

  // --- Người duyệt (quyền approve) ---
  approve: (id: number) => apiPost<VehicleBooking>(`${BASE_URL}/${id}/approve`, {}),
  /** Yêu cầu chỉnh sửa: trả phiếu về người tạo, kèm lý do. */
  returnForEdit: (id: number, reason: string) =>
    apiPost<VehicleBooking>(`${BASE_URL}/${id}/return`, { reason }),
  reject: (id: number, reason: string) =>
    apiPost<VehicleBooking>(`${BASE_URL}/${id}/reject`, { reason }),

  // --- Tài xế được phân (quyền write) ---
  driverAccept: (id: number) => apiPost<VehicleBooking>(`${BASE_URL}/${id}/driver/accept`, {}),
  driverReject: (id: number, reason: string) =>
    apiPost<VehicleBooking>(`${BASE_URL}/${id}/driver/reject`, { reason }),
  driverStart: (id: number) => apiPost<VehicleBooking>(`${BASE_URL}/${id}/driver/start`, {}),
  driverComplete: (id: number, payload: { distance_km?: number; cost?: number }) =>
    apiPost<VehicleBooking>(`${BASE_URL}/${id}/driver/complete`, payload),
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

/** Hồ sơ tài xế của chính người đăng nhập — để form TỰ LÁI tự điền GPLX. */
export interface MyDriverProfile {
  id: number
  name: string
  license_number: string
  license_class: string
}

export const dispatchOptionsApi = {
  vehicles: () =>
    apiGet<PaginatedResult<VehicleOption>>('/api/vehicles', { params: { page_size: 500 } }),
  // Tài xế cho ô điều phối được LỌC THEO VAI TRÒ ở backend (chỉ người thật sự là
  // tài xế: thuê ngoài + nội bộ giữ vai trò `booking_driver`) — khác danh mục đầy đủ.
  drivers: () => apiGet<PaginatedResult<DriverOption>>('/api/dispatch/drivers'),
  // Hồ sơ tài xế của chính mình (null nếu chưa là tài xế) — cho tự lái tự điền GPLX.
  myDriver: () => apiGet<MyDriverProfile | null>('/api/dispatch/my-driver'),
}
