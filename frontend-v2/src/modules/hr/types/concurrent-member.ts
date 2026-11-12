/**
 * Một người KIÊM NHIỆM ở một phòng — bản TÓM TẮT cho trang chi tiết phòng ban và sơ đồ tổ chức (duoc-CR-755,
 * giai đoạn 05). Khớp `concurrent_members_service.list_visible_members` của backend.
 *
 * Cố ý KHÔNG có điện thoại, email, ngày sinh: người xem chỉ thấy người của công ty khác ở mức "ai, làm gì,
 * từ khi nào"; thông tin liên lạc phải mở hồ sơ (và còn phải qua phạm vi + `employee_sensitive`).
 */
export interface ConcurrentMember {
  /** Id DÒNG kiêm nhiệm (không phải id nhân sự) — dùng làm khóa hàng. */
  id: number
  employee_id: number
  code: string
  full_name: string
  /** Nhãn chức vụ kiêm nhiệm CHỤP lúc lưu dòng; có thể rỗng. */
  position_label: string
  company_id: number
  company_name: string
  department_id: number
  department_name: string
  from_date: string | null
  to_date: string | null
  /** Mã DẪN XUẤT `ConcurrentStatus` (1 Sắp tới · 2 Đang hiệu lực · 3 Đã hết). */
  status: number
  status_label: string
  /** Tắt = chỉ ghi nhận, không mở phạm vi quyền — người xem thấy tên nhưng thường không mở được hồ sơ. */
  counts_scope: boolean
  primary_company_id: number
  primary_company_name: string
  primary_department_id: number
  primary_department_name: string
  /** `true` = người xem mở được HỒ SƠ ĐẦY ĐỦ (Q1); `false` = chỉ xem dòng này. */
  can_open: boolean
}

/** Trả về của `GET /api/employee-concurrents`. */
export interface ConcurrentMembersResult {
  items: ConcurrentMember[]
  total: number
  /** `true` = phòng có nhiều hơn trần 200 dòng, danh sách đã bị cắt. */
  truncated: boolean
}
