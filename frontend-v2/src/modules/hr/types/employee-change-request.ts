import type { EmployeeFamily } from './employee'

/**
 * YÊU CẦU SỬA HỒ SƠ do nhân viên tự khai (duoc-CR-676, C6 của `doc/erp/hrm/01-ho-so-nhan-su.md`).
 *
 * Nhân viên gửi ở Trang cá nhân; phòng Nhân sự duyệt rồi mới áp vào hồ sơ. Khác nhóm LIÊN HỆ
 * (bao-CR-508) vốn áp ngay không qua duyệt.
 *
 * Trạng thái là mã SỐ của bộ `EMPLOYEE_CHANGE_REQUEST_STATUS` (sinh từ backend, xem
 * `shared/constants/statuses.ts`) — KHÔNG khai lại danh sách ở đây.
 */

/** Ba nhóm trường phẳng gửi được. Hộ gia đình đi riêng (`families`) vì nó là cả một danh sách. */
export type ChangeRequestGroup = 'personal' | 'bank' | 'documents'

/** Giá trị một ô: chữ, số mã, ngày `YYYY-MM-DD`, hoặc `null` (ngày bỏ trống / bị che). */
export type ChangeRequestValue = string | number | null

export interface ChangeRequestItem {
  group: ChangeRequestGroup
  field: string
  /** Giá trị trên hồ sơ LÚC GỬI. */
  before: ChangeRequestValue
  /** Giá trị nhân viên đề nghị. */
  after: ChangeRequestValue
  /** Giá trị trên hồ sơ HIỆN TẠI — khác `before` nghĩa là hồ sơ đã bị sửa sau khi gửi. */
  current: ChangeRequestValue
  /** `true` = người xem thiếu quyền nhạy cảm, cả ba giá trị về `null`. */
  masked: boolean
}

/** Một dòng hộ gia đình như backend lưu trong yêu cầu (không có id/thứ tự). */
export type ChangeRequestFamilyRow = Omit<EmployeeFamily, 'id' | 'sort_order'>

export interface ChangeRequestFamilies {
  /** `null` khi `masked` — backend không gửi danh sách cho người thiếu quyền nhạy cảm. */
  before: ChangeRequestFamilyRow[] | null
  after: ChangeRequestFamilyRow[] | null
  /**
   * Danh sách đang có trên hồ sơ LÚC NÀY (`null` khi `masked`). Khác `before` nghĩa là phòng Nhân
   * sự đã sửa hộ gia đình sau lúc gửi — backend trả 409 khi duyệt (review M3, duoc-CR-676).
   * Tùy chọn để bản backend cũ chưa gửi khóa này vẫn chạy.
   */
  current?: ChangeRequestFamilyRow[] | null
  masked: boolean
}

export interface EmployeeChangeRequest {
  id: number
  employee_id: number
  employee_code: string
  employee_name: string
  /** Mã số `EMPLOYEE_CHANGE_REQUEST_STATUS`: 1 chờ duyệt · 2 đã duyệt · 3 từ chối · 4 đã rút. */
  status: number
  items: ChangeRequestItem[]
  families: ChangeRequestFamilies | null
  note: string
  reject_reason: string
  created_at: string
  created_by_name: string
  decided_at: string | null
  decided_by_name: string
  /** Người xem bấm Duyệt / Từ chối được không — backend đã tính (tự duyệt, thiếu quyền nhạy cảm). */
  can_decide: boolean
  /** Yêu cầu chạm ô nhạy cảm — duyệt cần `employee_sensitive.read`. */
  has_sensitive: boolean
}

/** Thân `POST /api/employees/me/change-requests` — CHỈ mang ô đã đổi. */
export interface ChangeRequestPayload {
  personal?: Record<string, ChangeRequestValue>
  bank?: Record<string, ChangeRequestValue>
  documents?: Record<string, ChangeRequestValue>
  /** Đổi thì gửi CẢ danh sách (thay thế toàn bộ, cùng luật `PUT /{id}/families`). */
  families?: ChangeRequestFamilyRow[]
  note?: string
}
