/**
 * Việc duyệt một nhân sự đang giữ — `GET /api/employees/{id}/pending-work` (duoc-CR-665, V0-4).
 * Khớp `backend/app/modules/employee/pending_work_service.py`.
 */
export interface PendingApprovalTask {
  task_id: number
  instance_id: number
  /** Loại chứng từ (`purchase_request`, `leave_request`…) — nhãn tra ở `ENTITY_LABELS` của phân hệ Duyệt. */
  entity: string
  entity_id: number
  entity_code: string
  entity_title: string
  /** Người xem không đọc được chứng từ này: mã/tên phiếu + người trình bị xóa trắng. */
  hidden?: boolean
  node_name: string
  /** 1 = chưa tới lượt · 2 = đang chờ người này. */
  status: number
  status_label: string
  due_at: string | null
  is_overdue: boolean
  started_by_employee_id: number
  started_by_name: string
}

export interface PendingFlowStep {
  flow_id: number
  flow_code: string
  flow_name: string
  entity: string
  node_id: number
  node_seq: number
  node_name: string
  /** `approver` = người duyệt cụ thể của bước · `fallback` = người dự phòng. */
  role: 'approver' | 'fallback'
}

export interface EmployeePendingWork {
  employee_id: number
  tasks: PendingApprovalTask[]
  total_tasks: number
  flow_steps: PendingFlowStep[]
  total_flow_steps: number
}
