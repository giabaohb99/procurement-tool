import type { PermissionMap } from '@/core/authorization/permission-types'

/** Hồ sơ người dùng do `/api/auth/login|refresh|me` trả về (payload `_me_payload`). */
export interface AuthUser {
  id: number
  email: string
  full_name: string
  employee_id?: number
  emp_code?: string
  company_id?: number
  company_name?: string
  avatar?: string
  signature?: string
  phone?: string
  department_id?: number
  department_name?: string
  /** Tên các vai trò thật (từ tab_user_role) — nối bằng dấu phẩy cũng có ở `role_name`. */
  role_name?: string
  role_names?: string[]
  position?: string
  /** Tên các phòng ban KIÊM NHIỆM (phòng phụ, không tính phòng chính). */
  kiem_nhiem?: string[]
  /**
   * Vai trò ĐANG GIỮ (id), không phải quyền — quyền nằm ở `permissions`.
   *
   * Màn Phân quyền dùng nó để khóa ma trận của chính vai trò mình đang giữ.
   * Backend đã chặn cửa đó (`core/privilege_escalation.py`), nhưng để người
   * dùng tick thoải mái rồi mới ăn 403 lúc bấm Lưu thì họ tưởng hệ hỏng chứ
   * không tưởng là có luật.
   */
  role_ids?: number[]
  /**
   * Tuỳ chọn HIỂN THỊ cá nhân, lưu ở `tab_user_preference` phía máy chủ nên đi
   * theo tài khoản chứ không theo trình duyệt. Hiện chỉ có `theme_preset`
   * (bảng màu giao diện — xem `@/shared/theme`).
   *
   * Kiểu là `Record<string, string>` chứ không liệt kê từng khoá: máy chủ nhận
   * khoá tuỳ ý, khai cứng ở đây thì thêm một tuỳ chọn phải sửa hai nơi.
   */
  preferences?: Record<string, string>
  permissions: PermissionMap
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  user: AuthUser
}

export interface LoginCredentials {
  /** Mã nhân viên HOẶC email — backend nhận cả hai. */
  username: string
  password: string
}
