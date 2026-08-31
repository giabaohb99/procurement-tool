/**
 * Kiểu & bộ mã của phân hệ Đặt xe nội bộ.
 *
 * Các cột nghĩa "loại / trạng thái" backend lưu SMALLINT (rule R2) và trả kèm số +
 * nhãn. Bản đối chiếu nhãn ở đây phải KHỚP `model.py` bên backend
 * (`REQUEST_TYPE_LABELS`, `BOOKING_STATUS_LABELS`, `DRIVER_STATUS_LABELS`).
 */

// --- Loại yêu cầu ---------------------------------------------------------
export const REQUEST_TYPE = {
  car: 1, // Đặt xe công tác (chở người)
  delivery: 2, // Đặt xe giao hàng (chở hàng)
} as const
export type RequestType = (typeof REQUEST_TYPE)[keyof typeof REQUEST_TYPE]

export const REQUEST_TYPE_LABELS: Record<number, string> = {
  [REQUEST_TYPE.car]: 'Đặt xe công tác',
  [REQUEST_TYPE.delivery]: 'Đặt xe giao hàng',
}

// --- Trạng thái chung -----------------------------------------------------
export const BOOKING_STATUS = {
  draft: 1,
  pending: 2,
  approved: 3,
  dispatched: 4,
  completed: 5,
  rejected: 6,
  cancelled: 7,
  returned: 8,
} as const
export type BookingStatus = (typeof BOOKING_STATUS)[keyof typeof BOOKING_STATUS]

export const BOOKING_STATUS_LABELS: Record<number, string> = {
  [BOOKING_STATUS.draft]: 'Nháp',
  [BOOKING_STATUS.pending]: 'Chờ duyệt',
  [BOOKING_STATUS.approved]: 'Đã duyệt',
  [BOOKING_STATUS.dispatched]: 'Điều phối',
  [BOOKING_STATUS.completed]: 'Hoàn thành',
  [BOOKING_STATUS.rejected]: 'Từ chối',
  [BOOKING_STATUS.cancelled]: 'Đã hủy',
  [BOOKING_STATUS.returned]: 'Yêu cầu chỉnh sửa',
}

/** Sắc thái badge theo trạng thái — dùng cho `<Badge variant>` / lớp màu. */
export const BOOKING_STATUS_TONE: Record<number, 'neutral' | 'info' | 'success' | 'warning' | 'danger'> = {
  [BOOKING_STATUS.draft]: 'neutral',
  [BOOKING_STATUS.pending]: 'warning',
  [BOOKING_STATUS.approved]: 'info',
  [BOOKING_STATUS.dispatched]: 'info',
  [BOOKING_STATUS.completed]: 'success',
  [BOOKING_STATUS.rejected]: 'danger',
  [BOOKING_STATUS.cancelled]: 'neutral',
  [BOOKING_STATUS.returned]: 'warning',
}

// --- Trạng thái tài xế ----------------------------------------------------
export const DRIVER_STATUS_LABELS: Record<number, string> = {
  0: '',
  1: 'Chờ tài xế',
  2: 'Đã nhận',
  3: 'Đang đi',
  4: 'Hoàn thành',
  5: 'Tài xế từ chối',
}

// --- Bản ghi phiếu (khớp VehicleBookingResponse) --------------------------
export interface VehicleBooking {
  id: number
  code: string
  request_type: number
  request_type_label: string
  purpose: string
  start_location: string
  end_location: string
  stops: string[]
  start_time: string
  end_time: string
  // Đặt xe công tác
  passenger_count: number
  attendees: string
  contact_phone: string
  is_round_trip: boolean
  // Giao hàng
  goods_name: string
  goods_size: string
  sender_name: string
  sender_phone: string
  receiver_name: string
  receiver_phone: string
  special_instructions: string
  // Phạm vi + người tạo
  department_id: number
  company_id: number
  first_approver_id: number
  requester: string
  requester_id: number
  status: number
  status_label: string
  note: string
  // Điều phối / chạy chuyến
  assigned_vehicle_id: number | null
  assigned_driver_id: number | null
  dispatched_by: number | null
  dispatched_at: string | null
  driver_status: number
  driver_status_label: string
  actual_start_time: string
  actual_end_time: string
  distance_km: number
  cost: number
  created_at: string | null
}

/** Payload tạo/sửa phiếu — mọi trường tùy chọn để form 2 loại dùng chung. */
export interface VehicleBookingPayload {
  request_type: number
  purpose: string
  start_location?: string
  end_location?: string
  stops?: string[]
  start_time?: string
  end_time?: string
  passenger_count?: number
  attendees?: string
  contact_phone?: string
  is_round_trip?: boolean
  goods_name?: string
  goods_size?: string
  sender_name?: string
  sender_phone?: string
  receiver_name?: string
  receiver_phone?: string
  special_instructions?: string
  first_approver_id?: number
  note?: string
}
