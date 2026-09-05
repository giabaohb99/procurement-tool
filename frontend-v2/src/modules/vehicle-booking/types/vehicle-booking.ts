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

/**
 * Tông màu badge dạng "pill" theo po_badges_design.md (gray/warn/ok/err/info).
 * Màu cụ thể của mỗi tông khai ở `components/status-pill.tsx` — đây chỉ là bản đồ
 * trạng thái → tông để bảng và popup dùng chung một quy ước.
 */
export type BadgeTone = 'gray' | 'warn' | 'ok' | 'err' | 'info'

export const BOOKING_STATUS_BADGE: Record<number, BadgeTone> = {
  [BOOKING_STATUS.draft]: 'gray', // Nháp
  [BOOKING_STATUS.pending]: 'warn', // Chờ duyệt
  [BOOKING_STATUS.approved]: 'ok', // Đã duyệt
  [BOOKING_STATUS.dispatched]: 'info', // Điều phối (đang xử lý)
  [BOOKING_STATUS.completed]: 'ok', // Hoàn thành
  [BOOKING_STATUS.rejected]: 'err', // Từ chối
  [BOOKING_STATUS.cancelled]: 'gray', // Đã hủy — kết thúc, trung tính
  [BOOKING_STATUS.returned]: 'warn', // Yêu cầu chỉnh sửa (bị trả lại)
}

// --- Trạng thái tài xế ----------------------------------------------------
export const DRIVER_STATUS = {
  none: 0,
  waiting: 1, // Chờ tài xế phản hồi
  accepted: 2, // Đã nhận
  ongoing: 3, // Đang đi
  completed: 4, // Hoàn thành
  rejected: 5, // Tài xế từ chối — quay về điều phối
} as const
export type DriverStatus = (typeof DRIVER_STATUS)[keyof typeof DRIVER_STATUS]

export const DRIVER_STATUS_LABELS: Record<number, string> = {
  [DRIVER_STATUS.none]: '',
  [DRIVER_STATUS.waiting]: 'Chờ tài xế',
  [DRIVER_STATUS.accepted]: 'Đã nhận',
  [DRIVER_STATUS.ongoing]: 'Đang đi',
  [DRIVER_STATUS.completed]: 'Hoàn thành',
  [DRIVER_STATUS.rejected]: 'Tài xế từ chối',
}

export const DRIVER_STATUS_BADGE: Record<number, BadgeTone> = {
  [DRIVER_STATUS.waiting]: 'warn', // Chờ tài xế
  [DRIVER_STATUS.accepted]: 'info', // Đã nhận
  [DRIVER_STATUS.ongoing]: 'info', // Đang đi
  [DRIVER_STATUS.completed]: 'ok', // Hoàn thành
  [DRIVER_STATUS.rejected]: 'err', // Tài xế từ chối
}

// --- Điểm dừng trung gian -------------------------------------------------
export interface Stop {
  location: string
  contact_name: string
  contact_phone: string
}

/** Điểm dừng rỗng để thêm dòng mới trên form. */
export function emptyStop(): Stop {
  return { location: '', contact_name: '', contact_phone: '' }
}

// --- Bản ghi phiếu (khớp VehicleBookingResponse) --------------------------
export interface VehicleBooking {
  id: number
  code: string
  request_type: number
  request_type_label: string
  /** Tự lái: người yêu cầu là tài xế (điều phối chỉ gán xe). */
  is_self_drive: boolean
  /** GPLX của người yêu cầu (khi tự lái). */
  license_number: string
  license_class: string
  purpose: string
  start_location: string
  end_location: string
  stops: Stop[]
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
  assigned_vehicle_label: string
  assigned_driver_label: string
  dispatched_by: number | null
  dispatched_at: string | null
  driver_status: number
  driver_status_label: string
  actual_start_time: string
  actual_end_time: string
  distance_km: number
  cost: number
  /** True khi người đang xem chính là tài xế được phân — bày nhóm nút của tài xế. */
  is_assigned_driver: boolean
  /** True khi phiếu đang chạy trong luồng duyệt nhiều bước — ẩn 3 nút duyệt cũ. */
  approval_running?: boolean
  created_at: string | null
}

/** Payload tạo/sửa phiếu — mọi trường tùy chọn để form 2 loại dùng chung. */
export interface VehicleBookingPayload {
  request_type: number
  is_self_drive?: boolean
  license_number?: string
  license_class?: string
  purpose: string
  start_location?: string
  end_location?: string
  stops?: Stop[]
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
