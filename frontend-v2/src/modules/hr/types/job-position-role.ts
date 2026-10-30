/** Một vai trò trong gói quyền mặc định của chức vụ (duoc-CR-653). */
export interface JobPositionRole {
  role_id: number
  role_code: string
  role_name: string
}

/** `GET/PUT /api/job-positions/{id}/roles`. */
export interface JobPositionRoleBundle {
  roles: JobPositionRole[]
  /** Số tài khoản ĐỦ ĐIỀU KIỆN nhận gói (tài khoản mở, hồ sơ còn làm) — con số trên nút "Áp lại". */
  eligible_holders: number
}

/** Kết quả "Áp lại cho người đang giữ chức vụ". */
export interface ApplyPositionRolesResult {
  holders: number
  changed_users: number
  granted: number
  revoked: number
  skipped_self: number
  /** Số vai trò trong gói bị bỏ qua vì người bấm không đủ quyền để cấp. */
  skipped_no_permission: number
}
