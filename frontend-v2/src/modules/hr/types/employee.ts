/** Nhân viên — khớp `EmployeeOut` của backend. */
export interface Employee {
  id: number
  code: string
  full_name: string
  email: string
  phone: string
  company_id: number
  department_id: number
  /** Vị trí / chức vụ — CHỈ là chữ, không liên quan tới phân quyền. */
  position: string
  /**
   * ⚠️ Cột cũ, KHÔNG còn dùng để cấp quyền (CR-022). Quyền nay chỉ gán ở màn
   * "Phân quyền tài khoản". Giữ lại vì dữ liệu cũ vẫn còn.
   */
  role_name: string
  status: string
  is_active: boolean
  department_name?: string | null
  manager_name?: string | null
  /** Lấy từ tài khoản đăng nhập (`tab_user.avatar`) — nguồn ảnh duy nhất. */
  avatar: string
}

/** Bản chi tiết — kèm id tài khoản đăng nhập (0 = nhân sự chưa được cấp tài khoản). */
export interface EmployeeDetail extends Employee {
  user_id: number
}

/**
 * Trạng thái nhân sự lưu thẳng CHUỖI TIẾNG VIỆT xuống DB (không phải mã enum),
 * nên danh sách này vừa là options của form vừa là giá trị thật gửi lên API.
 */
export const EMPLOYEE_STATUSES = [
  'Chính thức',
  'Cộng tác viên',
  'Nghỉ thai sản',
  'Nghỉ việc',
] as const

export type EmployeeStatus = (typeof EMPLOYEE_STATUSES)[number]

/**
 * "Trần Minh Được" -> "TĐ". Dùng khi chưa có ảnh đại diện.
 *
 * Bỏ qua các từ không bắt đầu bằng chữ cái: nhiều tên trong dữ liệu mẫu kết
 * thúc bằng "(Demo)", lấy thẳng ký tự đầu của từ cuối sẽ ra dấu ngoặc đơn.
 */
export function employeeInitials(fullName: string): string {
  const words = (fullName || '')
    .trim()
    .split(/\s+/)
    .filter((word) => /^\p{L}/u.test(word))

  const first = words.at(0)?.[0] ?? ''
  const last = words.length > 1 ? (words.at(-1)?.[0] ?? '') : ''
  return (first + last).toUpperCase() || '?'
}
