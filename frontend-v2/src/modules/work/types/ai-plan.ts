/**
 * Đề xuất kế hoạch AI chờ duyệt (kh-AI1-3, doc `erp/tai-lieu-ai/22` §5.2).
 *
 * AI soạn bằng `draft_work_plan`, người hỏi xác nhận → máy chủ lưu một ĐỀ XUẤT, chưa
 * tạo việc. Màn *Duyệt kế hoạch AI* cho chính người hỏi sửa người / giờ / dòng rồi
 * bấm Duyệt — lúc đó máy chủ mới dựng bảng Dự án.
 */

/** Mã `ai_plan_status` — khớp `AI_PLAN_STATUS` sinh ở `shared/constants/statuses.ts`. */
export const AI_PLAN_STATUS_PENDING = 1
export const AI_PLAN_STATUS_APPROVED = 2
export const AI_PLAN_STATUS_REJECTED = 3

/** Ba mức ưu tiên máy chủ nhận; giá trị lạ bị máy chủ đổi về "Thường". */
export const AI_PLAN_PRIORITIES = ['Gấp', 'Ưu tiên', 'Thường'] as const
export type AiPlanPriority = (typeof AI_PLAN_PRIORITIES)[number]

export interface AiPlanAssignee {
  employee_id: number
  code: string
  name: string
}

export interface AiPlanTaskType {
  id: number
  name: string
}

/** Một việc con — cùng khuôn việc, không có `subtasks`. */
export interface AiPlanSubtask {
  /** Máy chủ đặt (`p1t1s1`, `n3`…); dòng người thêm mới để RỖNG. */
  key: string
  title: string
  description: string
  assignees: AiPlanAssignee[]
  start_date: string
  due_date: string
  priority: string
  criteria: string[]
  estimate_hours: number | null
  task_type: AiPlanTaskType | null
  assignee_reason: string
}

export interface AiPlanTask extends AiPlanSubtask {
  subtasks: AiPlanSubtask[]
}

export interface AiPlanPhase {
  name: string
  tasks: AiPlanTask[]
}

export interface AiPlanCounts {
  phases?: number
  tasks?: number
  subtasks?: number
}

export interface AiPlanDocument {
  title: string
  description: string
  deadline: string
  phases: AiPlanPhase[]
  assumptions: string[]
  counts?: AiPlanCounts
}

/** Một dòng của `GET /api/ai-plans`. */
export interface AiPlanSummary {
  id: number
  status: number
  status_label: string
  title: string
  deadline: string | null
  channel_label: string
  counts: AiPlanCounts
  created_at: string | null
  list_id: number
  list_url: string | null
}

/** `GET /api/ai-plans/{id}`. */
export interface AiPlanDetail extends AiPlanSummary {
  goal: string
  /** Bản người sửa nếu có, không thì bản AI. */
  plan: AiPlanDocument
  plan_ai: AiPlanDocument | null
  plan_final: AiPlanDocument | null
  reject_reason: string
  decided_at: string | null
}

/**
 * Một lỗi trong `details.problems` của 422 `PLAN_INVALID`. `phase` / `task` / `subtask`
 * là VỊ TRÍ trong mảng đã gửi (đếm từ 0); `subtask` null = lỗi ở việc cha; cả ba null
 * = lỗi cấp kế hoạch.
 */
export interface AiPlanProblem {
  phase: number | null
  task: number | null
  subtask: number | null
  key: string
  field: string
  message: string
}

export interface AiPlanApproveResult {
  id: number
  list_id: number
  list_url: string
}
