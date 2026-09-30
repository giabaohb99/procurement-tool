export interface CategoryAssignee {
  id: number
  item_group_id: number
  item_group_name?: string | null
  primary_employee_id: number
  primary_name?: string | null
  primary_code?: string | null
  /** bao-CR-527: tình trạng HIỆN TẠI của NSTM chính — mã, nhãn và cờ đang hoạt động. */
  primary_status?: string | null
  primary_status_label?: string | null
  primary_is_active?: boolean | null
  /** bao-CR-527: NSTM chính không còn «Chính thức» / đã tắt hồ sơ → màn danh sách gắn cảnh báo. */
  primary_not_official?: boolean
  backup_employee_id: number
  backup_name?: string | null
  backup_code?: string | null
  /**
   * Phòng áp dụng. bao-CR-524: bộ dùng cho mọi phòng chưa có bộ riêng là bộ của phòng thu mua mặc
   * định («Sản xuất -Thu mua») — backend trả id + tên THẬT, kể cả dòng `0` («Thu mua chung» cũ).
   */
  department_id?: number
  department_name?: string | null
  created_at?: string
  updated_at?: string
}

export interface CategoryAssigneeBulkPayload {
  item_group_ids: number[]
  primary_employee_id: number
  backup_employee_id?: number
  /** Bỏ trống / 0 = phòng thu mua mặc định (bao-CR-524: backend ghi id thật). */
  department_id?: number
}
