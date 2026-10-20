/**
 * Hợp đồng JSON của `/api/feature-usage` (duoc-CR-655). Chỉ có số đã gom theo chức năng / phòng ban —
 * KHÔNG có `user_id` hay tên người. `code` là mã `UiAction` / `UiForm` (nhãn lấy từ bộ mã sinh), `route` là route mẫu không id.
 */
export interface FeatureRow {
  kind: number
  code: number
  route: string
  /** Số người KHÁC NHAU trong kỳ. */
  users: number
  /** Lượt bấm / lượt mở form / lượt xem / lượt tìm / số lỗi — theo `kind`. */
  uses: number
  completes: number
  abandons: number
  /** Tìm kiếm: số lượt không ra kết quả. */
  fails: number
  duration_ms: number
}

export interface FeatureSummary {
  period: { date_from: string; date_to: string }
  /** Ngày đầu tiên có số liệu; null = chưa từng thu. */
  tracking_since: string | null
  has_data: boolean
  /** Mẫu số cho «% người dùng»: số người có hoạt động trong kỳ. */
  active_users: number
  actions: FeatureRow[]
  forms: FeatureRow[]
  screens: FeatureRow[]
  searches: FeatureRow[]
  errors: FeatureRow[]
  unused_actions: number[]
  unused_forms: number[]
}

export interface FeatureDepartmentRow extends FeatureRow {
  department_id: number
  department_name: string
}

export interface FeatureBreakdown {
  kind: number
  code: number
  route: string
  by_department: FeatureDepartmentRow[]
  by_route: FeatureRow[]
}
