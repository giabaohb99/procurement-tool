/** Tài khoản đăng nhập — khớp `UserOut` + các trường controller bồi thêm. */
export interface UserAccount {
  id: number
  email: string
  /** 0 = tài khoản không gắn hồ sơ nhân sự nào. */
  employee_id: number
  is_active: boolean
  role_ids: number[]
  /** Lấy từ hồ sơ nhân sự; không có thì controller trả về email. */
  full_name: string
  department_name: string
  /** Mã nhân sự (chỉ có ở danh sách; rỗng khi tài khoản không còn hồ sơ). */
  code?: string
  /** SĐT của hồ sơ nhân sự (tìm & tự điền tài xế nội bộ). */
  phone?: string
  /** Email LIÊN HỆ của nhân sự (khác `email` = email đăng nhập). */
  contact_email?: string
  /** Ảnh đại diện (cùng ảnh tài khoản đăng nhập); rỗng thì hiện chữ viết tắt. */
  avatar?: string
  /** Chỉ có ở danh sách: hồ sơ nhân sự đã bị xóa -> tài khoản không còn hồ sơ. */
  is_orphan?: boolean
}

/**
 * Phạm vi dữ liệu của MỘT cặp (tài khoản × vai trò) — trục thứ hai của hệ phân
 * quyền. Mảng rỗng = KHÔNG giới hạn chiều đó, không phải "không thấy gì".
 *
 * Phòng ban định danh bằng TÊN (chuỗi) chứ không phải id — đúng theo
 * `ScopeUpdate` của backend.
 */
export interface UserScope {
  companies: number[]
  departments: string[]
  employees: number[]
  exclude_companies: number[]
  exclude_departments: string[]
  exclude_employees: number[]
}

export const EMPTY_USER_SCOPE: UserScope = {
  companies: [],
  departments: [],
  employees: [],
  exclude_companies: [],
  exclude_departments: [],
  exclude_employees: [],
}

/** Bộ lọc "Tình trạng" của danh sách tài khoản. */
export type UserAccountFlag = '' | 'no_role' | 'orphan'
