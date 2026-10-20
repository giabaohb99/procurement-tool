/**
 * Hợp đồng JSON của `/api/work-capability` (duoc-CR-657). Thời gian tính bằng NGÀY LỊCH, tỷ lệ là số 0..1.
 * Dưới ngưỡng mẫu (`below_threshold`) mọi số là `null` — hiện «chưa đủ mẫu», không điền 0.
 * Dòng ước tính (`n_estimated`) không bao giờ nằm trong trung vị / p90.
 */
export interface CapabilityStats {
  n_done: number
  /** Số phiếu xong nhưng mốc xong là ƯỚC (không có nhật ký) — loại khỏi mọi số bên dưới. */
  n_estimated: number
  below_threshold: boolean
  mean_days: number | null
  p50_days: number | null
  p90_days: number | null
  max_days: number | null
  /** Số lần làm lại trung bình trên mỗi phiếu. */
  rework_rate: number | null
  first_pass_rate: number | null
  late_rate: number | null
  /** Trung vị (giờ thực tế / giờ ước lượng) của các việc có đủ hai số. */
  est_ratio_p50: number | null
}

export interface CapabilityTypeRow extends CapabilityStats {
  kind: number
  kind_label: string
  task_type_id: number
  task_type_name: string
}

export interface CapabilityPersonRow extends CapabilityTypeRow {
  employee_id: number
  employee_code: string
  full_name: string
  department_id: number
}

export interface CapabilitySummary {
  period: { date_from: string; date_to: string }
  types: CapabilityTypeRow[]
  people: CapabilityPersonRow[]
  n_estimated: number
  min_samples: number
  truncated: boolean
}

/** Tải đang ôm của một người — các số THÀNH PHẦN, không có điểm tổng có trọng số. */
export interface WorkLoadRow {
  employee_id: number
  employee_code: string
  full_name: string
  company_id: number
  department_id: number
  approvals_pending: number
  approvals_overdue: number
  delegated_in: number
  delegated_in_overdue: number
  work_open: number
  work_overdue: number
  work_estimate_hours_open: number
  pr_handling: number
  pr_approval_pending: number
  po_handling: number
  survey_lines_handling: number
  docs_pending_issue: number
  on_leave_today: boolean
  leave_days_ahead: number
  open_items_total: number
}

export interface WorkLoadResult {
  items: WorkLoadRow[]
  count: number
  horizon_days: number
}
