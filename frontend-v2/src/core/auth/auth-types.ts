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
  role_name?: string
  position?: string
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
