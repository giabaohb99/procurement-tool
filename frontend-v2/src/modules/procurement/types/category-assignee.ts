export interface CategoryAssignee {
  id: number
  item_group_id: number
  item_group_name?: string | null
  primary_employee_id: number
  primary_name?: string | null
  primary_code?: string | null
  backup_employee_id: number
  backup_name?: string | null
  backup_code?: string | null
  /** bao-CR-414 GĐ2: 0 = bộ «Thu mua chung», áp cho mọi phòng chưa có dòng riêng. */
  department_id?: number
  department_name?: string | null
  created_at?: string
  updated_at?: string
}

export interface CategoryAssigneeBulkPayload {
  item_group_ids: number[]
  primary_employee_id: number
  backup_employee_id?: number
  /** Bỏ trống = 0 = Thu mua chung. */
  department_id?: number
}

/** Nhãn của bộ phân công chung (department_id = 0). */
export const SHARED_DEPARTMENT_LABEL = 'Thu mua chung'
