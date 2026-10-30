/**
 * Danh sách BIẾN của mẫu hợp đồng lao động (duoc-CR-630). Khớp `VariableOut` của backend.
 * Mã số `source` / `value_type` lấy từ `LABOR_CONTRACT_VARIABLE_SOURCE` / `_TYPE` trong
 * `@/shared/constants/statuses` (sinh từ backend) — đừng gõ lại nhãn ở đây.
 */

/** `LaborContractVariableSource` của backend. */
export const VARIABLE_SOURCE_SYSTEM = 1
export const VARIABLE_SOURCE_CUSTOM = 2

/** `LaborContractVariableType` của backend. */
export const VARIABLE_TYPE_TEXT = 1
export const VARIABLE_TYPE_MULTILINE = 2
export const VARIABLE_TYPE_NUMBER = 3
export const VARIABLE_TYPE_DATE = 4
export const VARIABLE_TYPE_MONEY = 5

export interface LaborContractVariable {
  id: number
  code: string
  source: number
  value_type: number
  label: string
  description: string
  example: string
  /** Dạng CHUẨN của kiểu (tiền "15000000", số "1.5", ngày "2026-10-01"). */
  default_value: string
  is_required: boolean
  is_active: boolean
  is_hidden: boolean
  sort_order: number
  /** Số mẫu (mọi pháp nhân) đang chứa biến. */
  template_count: number
  group: string
  created_at: string | null
  created_by_name: string
}

export interface LaborContractVariableList {
  total: number
  items: LaborContractVariable[]
  /** Quyền GHI (thêm / sửa) = có `write` VÀ phạm vi "tất cả pháp nhân" — backend tính. */
  can_manage: boolean
  /** Quyền XÓA = có `delete` VÀ phạm vi "tất cả pháp nhân". */
  can_delete: boolean
}

export interface LaborContractVariableUsage {
  /** Chỉ mẫu người xem thấy theo phạm vi. */
  templates: { id: number; name: string; company_name: string }[]
  template_count: number
  hidden_template_count: number
  contract_count: number
}

export interface LaborContractVariableDetail extends LaborContractVariable {
  usage: LaborContractVariableUsage
  /** Đã dùng (hoặc là biến hệ thống) → không đổi được mã / kiểu. */
  code_locked: boolean
}

/** Ô nhập biến tùy chỉnh trong hộp Lập / Sửa hợp đồng. */
export interface LaborContractInputField {
  code: string
  label: string
  description: string
  value_type: number
  default_value: string
  is_required: boolean
  is_active: boolean
  sort_order: number
}

export interface LaborContractVariableCreatePayload {
  code: string
  label: string
  description: string
  example: string
  value_type: number
  default_value: string
  is_required: boolean
  is_active: boolean
  sort_order: number
}

/** PATCH: biến hệ thống chỉ nhận `label` / `description` / `is_hidden`. */
export type LaborContractVariableUpdatePayload = Partial<LaborContractVariableCreatePayload> & {
  is_hidden?: boolean
}
