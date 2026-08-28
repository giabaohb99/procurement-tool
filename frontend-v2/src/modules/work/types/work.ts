/**
 * Phân hệ Công việc — kiểu dữ liệu khớp với `app/modules/work/serializer.py`.
 *
 * Bốn bộ số dưới đây là bản sao của `IntEnum` ở backend
 * (`app/modules/work/model.py`). Chúng KHÔNG lấy từ `shared/constants/statuses.ts`
 * vì tệp sinh tự động đó chỉ chứa bộ mã CHUỖI của QĐ-9 — xem ghi chú ở đầu
 * `model.py` bên backend. Đổi số ở backend thì phải sửa tay ở đây.
 */

export const WORK_TASK_STATUS = { OPEN: 1, DONE: 2, CANCELLED: 3 } as const

/** Số nhỏ = quyền TO (Q9) — mọi phép so quyền ở giao diện đều là `<=`. */
export const WORK_ROLE = { OWNER: 1, ADMIN: 2, MEMBER: 3, VIEWER: 4 } as const

export const WORK_PRIORITY = { NONE: 0, P1: 1, P2: 2, P3: 3, P4: 4 } as const

export const WORK_ASSIGNEE_KIND = { PIC: 1, FOLLOWER: 2 } as const

export const WORK_ROLE_LABELS: Record<number, string> = {
  [WORK_ROLE.OWNER]: 'Chủ sở hữu',
  [WORK_ROLE.ADMIN]: 'Quản trị',
  [WORK_ROLE.MEMBER]: 'Thành viên',
  [WORK_ROLE.VIEWER]: 'Khách xem',
}

export const WORK_PRIORITY_LABELS: Record<number, string> = {
  [WORK_PRIORITY.NONE]: 'Không đặt',
  [WORK_PRIORITY.P1]: 'P1 — Khẩn',
  [WORK_PRIORITY.P2]: 'P2 — Cao',
  [WORK_PRIORITY.P3]: 'P3 — Vừa',
  [WORK_PRIORITY.P4]: 'P4 — Thấp',
}

export const WORK_STATUS_LABELS: Record<number, string> = {
  [WORK_TASK_STATUS.OPEN]: 'Đang mở',
  [WORK_TASK_STATUS.DONE]: 'Hoàn thành',
  [WORK_TASK_STATUS.CANCELLED]: 'Đã hủy',
}

export interface WorkGroup {
  id: number
  name: string
  description: string
  parent_id: number | null
  sort_order: number
  is_archived: number
  my_role: number | null
}

export interface WorkList {
  id: number
  name: string
  description: string
  color: string
  group_id: number | null
  sort_order: number
  is_archived: number
  my_role: number | null
  task_count: number
  /** Số việc đã hoàn thành — tử số của thanh tiến độ trên màn liệt kê dự án. */
  task_done: number
  created_at: string
  /**
   * Chủ sở hữu và thành viên CHỈ có khi gọi `/api/work/lists?with_people=1`
   * (màn liệt kê dự án). Cây điều hướng và bảng kanban không xin nên luôn nhận
   * `null` / `[]` — đừng đọc như "dự án không có chủ".
   */
  owner: WorkMember | null
  members: WorkMember[]
}

/** Một nhánh của cây điều hướng bên trái (A-05). */
export interface WorkGroupNode extends WorkGroup {
  lists: WorkList[]
  children: WorkGroupNode[]
}

export interface WorkSidebar {
  groups: WorkGroupNode[]
  /** List không thuộc nhóm nào — hợp lệ, hiện ở đáy cây (A-08). */
  lists: WorkList[]
}

export interface WorkMember {
  id: number
  employee_id: number
  role: number
  department_id: number | null
  employee_name: string
  employee_code: string
}

export interface WorkSection {
  id: number
  list_id: number
  name: string
  color: string
  sort_order: number
}

export interface WorkTag {
  id: number
  list_id: number
  name: string
  color: string
  sort_order: number
}

export interface WorkLabelOption {
  id: number
  field_id: number
  name: string
  color: string
  sort_order: number
}

export interface WorkLabelField {
  id: number
  list_id: number
  name: string
  sort_order: number
  options: WorkLabelOption[]
}

export interface WorkAssignee {
  employee_id: number
  kind: number
  employee_name: string
  employee_code: string
}

export interface WorkTask {
  id: number
  list_id: number
  section_id: number | null
  parent_id: number | null
  title: string
  description: string
  status: number
  priority: number
  start_date: string
  due_date: string
  sort_order: number
  creator_employee_id: number
  completed_at: string | null
  completed_by: number | null
  created_at: string
  updated_at: string
  assignees: WorkAssignee[]
  tag_ids: number[]
  labels: { field_id: number; option_id: number }[]
  subtask_done: number
  subtask_total: number
  comment_count: number
  /** Chỉ có ở `GET /tasks/{id}` — panel chi tiết (D-03). */
  subtasks?: WorkTask[]
}

export interface WorkBoard {
  list: WorkList
  sections: WorkSection[]
  /** CHỈ task cha: việc con không bao giờ thành thẻ trên bảng (C-05). */
  tasks: WorkTask[]
}
