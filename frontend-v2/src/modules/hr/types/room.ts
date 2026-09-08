/**
 * Kiểu dữ liệu của ĐẶT PHÒNG HỌP (duoc-CR-279).
 *
 * ⚠️ Bộ mã gõ TAY ở đây, cố ý — `gen_status_ts.py` chỉ sinh cho bộ mã CHUỖI,
 * còn đây là bộ mã SỐ (R2/QĐ-11). Nguồn chân lý là
 * `backend/app/modules/meeting_room/constants.py`; đổi bên đó thì đổi cả ở đây.
 * Cùng cách làm với `types/leave.ts`.
 */

export const ROOM_BOOKING_STATUS = {
  DRAFT: 1,
  PENDING: 2,
  APPROVED: 3,
  REJECTED: 4,
  RETURNED: 5,
  CANCELLED: 6,
} as const

export type RoomBookingStatus =
  (typeof ROOM_BOOKING_STATUS)[keyof typeof ROOM_BOOKING_STATUS]

export const ROOM_BOOKING_STATUS_LABELS: Record<number, string> = {
  [ROOM_BOOKING_STATUS.DRAFT]: 'Nháp',
  [ROOM_BOOKING_STATUS.PENDING]: 'Chờ duyệt',
  [ROOM_BOOKING_STATUS.APPROVED]: 'Đã duyệt',
  [ROOM_BOOKING_STATUS.REJECTED]: 'Từ chối',
  [ROOM_BOOKING_STATUS.RETURNED]: 'Trả về chỉnh sửa',
  [ROOM_BOOKING_STATUS.CANCELLED]: 'Đã hủy',
}

/** Sửa được khi chưa vào luồng hoặc vừa bị trả về — khớp `EDITABLE_STATUSES` backend. */
export const EDITABLE_ROOM_STATUSES: number[] = [
  ROOM_BOOKING_STATUS.DRAFT,
  ROOM_BOOKING_STATUS.RETURNED,
]

/**
 * Trạng thái đang GIỮ phòng. Dùng để tô màu trên lịch: chỉ hai trạng thái này
 * mới chiếm chỗ thật, còn nháp/hủy/từ chối thì không được vẽ như đã chiếm.
 */
export const BLOCKING_ROOM_STATUSES: number[] = [
  ROOM_BOOKING_STATUS.PENDING,
  ROOM_BOOKING_STATUS.APPROVED,
]

/**
 * ⚠️ Khai bằng **`type` chứ không `interface`** — `CrudConfig<T>` đòi `T` thoả
 * `Record<string, unknown>`, mà TypeScript chỉ suy ra chỉ mục ngầm cho type
 * alias; `interface` thì không và typecheck đỏ. Cùng bẫy đã gặp với `LeaveType`.
 */
export type MeetingRoom = {
  id: number
  code: string
  name: string
  /** `0` = phòng dùng chung mọi pháp nhân (toà nhà chung). */
  company_id: number
  location: string
  capacity: number
  equipment: string
  is_active: boolean
  sort_order: number
  note: string
}

export interface RoomBookingAttendee {
  id: number
  employee_id: number
  employee_name: string
  role: string
  sort_order: number
}

export interface RoomBooking {
  id: number
  code: string
  room_id: number
  room_name: string
  room_code: string
  company_id: number
  department_id: number
  requester_employee_id: number
  requester_name: string
  title: string
  purpose: string
  /** ISO có giờ — `2026-09-10T09:00:00`. */
  start_at: string
  end_at: string
  attendee_count: number
  status: number
  status_label: string
  /** `0` = chưa gửi duyệt, hoặc môi trường chưa khai luồng nào. */
  approval_instance_id: number
  submitted_at: string | null
  decided_at: string | null
  decision_note: string
  /** Chỉ có ở đường lấy MỘT phiếu. */
  attendees?: RoomBookingAttendee[]
}

/** Một dòng của `/availability` — phòng kèm những phiếu đang giữ nó. */
export interface RoomAvailability {
  room_id: number
  room_code: string
  room_name: string
  location: string
  capacity: number
  equipment: string
  available: boolean
  bookings: {
    id: number
    code: string
    title: string
    start_at: string
    end_at: string
    status: number
  }[]
}

export interface RoomBookingPayload {
  room_id: number
  title: string
  start_at: string
  end_at: string
  purpose?: string
  attendee_count?: number
  requester_employee_id?: number
  attendees?: { employee_id: number; role?: string }[]
}

/**
 * Một dòng trong hộp việc duyệt (`/inbox/to-approve` · `/inbox/handled`) — phiếu
 * kèm VIỆC của tôi trên nó và luồng duyệt dạng chữ.
 *
 * `task.instance_id` chính là thứ nút Duyệt / Trả về / Từ chối gọi tới; không có
 * nó thì giao diện phải đi hỏi lại phiên duyệt thêm một lượt.
 */
export interface RoomInboxRow extends RoomBooking {
  task: {
    id: number
    instance_id: number
    node_seq: number
    node_name: string
    status: number
    due_at: string | null
    decided_at: string | null
    action?: string
    action_label?: string
    note?: string
    at?: string
  }
  flow?: { text: string; current_seq: number; total: number } | null
}
