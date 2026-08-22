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
  created_at?: string
  updated_at?: string
}

export interface CategoryAssigneeBulkPayload {
  item_group_ids: number[]
  primary_employee_id: number
  backup_employee_id?: number
}
