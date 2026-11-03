/**
 * CHÍNH SÁCH NGHỈ PHÉP + PHÂN BỔ CHÍNH SÁCH (duoc-CR-717) — kiểu gõ tay theo hợp đồng API của
 * `backend/app/modules/leave/policy_*_controller.py`.
 *
 * Chính sách = một gói "loại nghỉ → số ngày mỗi năm". Phân bổ = gán gói cho MỘT nhân sự trong một
 * khoảng ngày. Loại nghỉ không có trong gói vẫn cấp theo hạn mức của loại nghỉ (D1a).
 */

/**
 * Trạng thái phân bổ — DẪN XUẤT theo ngày ở backend (`LeavePolicyAssignmentState`), không lưu.
 * Màn hình chỉ ĐỌC `state`, không tự so ngày ở TypeScript (đồng hồ máy khách có thể lệch ngày VN).
 */
export const LEAVE_POLICY_ASSIGNMENT_STATE = {
  UPCOMING: 1,
  ACTIVE: 2,
  ENDED: 3,
} as const

export type LeavePolicyAssignmentState =
  (typeof LEAVE_POLICY_ASSIGNMENT_STATE)[keyof typeof LEAVE_POLICY_ASSIGNMENT_STATE]

export const LEAVE_POLICY_ASSIGNMENT_STATE_LABELS: Record<LeavePolicyAssignmentState, string> = {
  [LEAVE_POLICY_ASSIGNMENT_STATE.UPCOMING]: 'Sắp tới',
  [LEAVE_POLICY_ASSIGNMENT_STATE.ACTIVE]: 'Đang hiệu lực',
  [LEAVE_POLICY_ASSIGNMENT_STATE.ENDED]: 'Đã kết thúc',
}

/** `type` chứ không `interface` — `CrudConfig<T>` cần chỉ mục ngầm, xem ghi chú ở `LeaveType`. */
export type LeavePolicy = {
  id: number
  code: string
  name: string
  note: string
  is_active: boolean
}

export interface LeavePolicyLine {
  id?: number
  leave_type_id: number
  annual_days: number
}

export interface LeavePolicyAssignment {
  id: number
  employee_id: number
  company_id: number
  policy_id: number
  effective_from: string
  /** `null` = không thời hạn. */
  effective_to: string | null
  note: string
  employee_name: string
  employee_code: string
  policy_name: string
  state: LeavePolicyAssignmentState
  updated_at?: string | null
}

/** Một loại nghỉ đổi hạn mức năm nay: `before` = số đang cấp (hoặc sẽ cấp nếu chưa có dòng). */
export interface PolicyQuotaChange {
  leave_type_id: number
  before: number
  after: number
  /** Chỉ có ở kết quả HÀNG LOẠT. */
  employee_id?: number
}

export interface PolicyNegativeAfter {
  leave_type_id: number
  available_days: number
  employee_id?: number
}

/** Kết quả đụng quỹ năm nay của một lượt ghi phân bổ. */
export interface PolicyBalanceChanges {
  created: number
  recalculated: PolicyQuotaChange[]
  kept: number
  negative_after: PolicyNegativeAfter[]
}

/**
 * Lý do không phân bổ được: chồng ngày · tự phân bổ cho mình · gói đã ngừng · ngoài phạm vi (người nằm
 * ngoài phạm vi ghi quỹ phép / đã nghỉ việc / không tồn tại — chỉ xem trước theo `employee_ids` mới có;
 * dòng đó có `code`/`name` rỗng và `current: null`, chỉ `conflict_message` là có nghĩa).
 */
export type PolicyConflict = 'overlap' | 'self' | 'inactive' | 'scope'

export interface PolicyPreviewItem {
  employee_id: number
  code: string
  name: string
  department_name: string
  hire_date: string | null
  current: { policy_name: string; from: string; to: string | null } | null
  conflict: PolicyConflict | null
  conflict_message: string
  changes: PolicyQuotaChange[]
}

export interface PolicyPreviewResult {
  items: PolicyPreviewItem[]
  total: number
  /** Quá 500 người — chỉ trả 500 người đầu (theo mã). */
  truncated: boolean
}

export interface PolicyBulkResult {
  created: number
  skipped: { employee_id: number; name: string; reason: string }[]
  balances: PolicyBalanceChanges
}

// ── Thân request ─────────────────────────────────────────────────────────────

interface AssignmentRangePayload {
  policy_id: number
  effective_from: string
  effective_to: string | null
  close_previous: boolean
}

export interface PolicyPreviewPayload extends AssignmentRangePayload {
  employee_ids?: number[]
  company_id?: number
  department_id?: number
  employment_type?: number
  job_level?: number
  only_without_active?: boolean
}

export interface PolicyAssignPayload extends AssignmentRangePayload {
  employee_id: number
  note: string
  recalc_current_year: boolean
}

export interface PolicyBulkPayload extends AssignmentRangePayload {
  employee_ids: number[]
  recalc_current_year: boolean
}

export interface PolicyAssignmentUpdatePayload {
  effective_to: string | null
  recalc_current_year: boolean
  note?: string
}
