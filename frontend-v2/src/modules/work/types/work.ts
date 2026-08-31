/**
 * Phân hệ Công việc — kiểu dữ liệu khớp với `app/modules/work/serializer.py`.
 *
 * Bốn bộ số dưới đây là bản sao của `IntEnum` ở backend
 * (`app/modules/work/model.py`). Chúng KHÔNG lấy từ `shared/constants/statuses.ts`
 * vì tệp sinh tự động đó chỉ chứa bộ mã CHUỖI của QĐ-9 — xem ghi chú ở đầu
 * `model.py` bên backend. Đổi số ở backend thì phải sửa tay ở đây.
 */

export const WORK_TASK_STATUS = { OPEN: 1, DONE: 2, CANCELLED: 3 } as const

/**
 * Việc thường hay CỘT MỐC (B-14). Cột mốc là một task như mọi task khác, chỉ
 * khác cách đọc ngày: chỉ `due_date` có nghĩa, và Gantt vẽ nó thành hình thoi.
 */
export const WORK_TASK_KIND = { TASK: 1, MILESTONE: 2 } as const

/** Bốn kiểu phụ thuộc việc trước–sau (B-15) — bộ của DHTMLX/MS Project. */
export const WORK_LINK_TYPE = { FS: 1, SS: 2, FF: 3, SF: 4 } as const

export type WorkLinkTypeValue = (typeof WORK_LINK_TYPE)[keyof typeof WORK_LINK_TYPE]

/** Số nhỏ = quyền TO (Q9) — mọi phép so quyền ở giao diện đều là `<=`. */
export const WORK_ROLE = { OWNER: 1, ADMIN: 2, MEMBER: 3, VIEWER: 4 } as const

export const WORK_ASSIGNEE_KIND = { PIC: 1, FOLLOWER: 2 } as const

export const WORK_ROLE_LABELS: Record<number, string> = {
  [WORK_ROLE.OWNER]: 'Chủ sở hữu',
  [WORK_ROLE.ADMIN]: 'Quản trị',
  [WORK_ROLE.MEMBER]: 'Thành viên',
  [WORK_ROLE.VIEWER]: 'Khách xem',
}

/** Nhãn ngắn cho menu chọn kiểu mũi tên — chữ đọc "đầu việc trước → đầu việc sau". */
export const WORK_LINK_TYPE_LABELS: Record<number, string> = {
  [WORK_LINK_TYPE.FS]: 'Xong → Bắt đầu',
  [WORK_LINK_TYPE.SS]: 'Bắt đầu → Bắt đầu',
  [WORK_LINK_TYPE.FF]: 'Xong → Xong',
  [WORK_LINK_TYPE.SF]: 'Bắt đầu → Xong',
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

export interface WorkLabelOption {
  id: number
  field_id: number
  name: string
  color: string
  sort_order: number
}

/**
 * Sáu kiểu trường tùy biến (B-13) — bản sao của `WorkLabelFieldType` ở
 * `backend/app/modules/work/model.py`. Đổi số bên đó thì phải sửa tay ở đây.
 */
export const WORK_FIELD_TYPE = {
  SINGLE: 1,
  MULTI: 2,
  PERSON: 3,
  NUMBER: 4,
  DATE: 5,
  TEXT: 6,
} as const

export type WorkFieldType = (typeof WORK_FIELD_TYPE)[keyof typeof WORK_FIELD_TYPE]

export const WORK_FIELD_TYPES: { value: WorkFieldType; label: string }[] = [
  { value: WORK_FIELD_TYPE.SINGLE, label: 'Chọn một giá trị' },
  { value: WORK_FIELD_TYPE.MULTI, label: 'Chọn nhiều giá trị' },
  { value: WORK_FIELD_TYPE.PERSON, label: 'Người' },
  { value: WORK_FIELD_TYPE.NUMBER, label: 'Số' },
  { value: WORK_FIELD_TYPE.DATE, label: 'Ngày' },
  { value: WORK_FIELD_TYPE.TEXT, label: 'Chữ' },
]

/** Hai kiểu duy nhất có bộ giá trị đặt sẵn — bốn kiểu kia nhập tự do. */
export function fieldHasOptions(type: number): boolean {
  return type === WORK_FIELD_TYPE.SINGLE || type === WORK_FIELD_TYPE.MULTI
}

export interface WorkLabelField {
  id: number
  list_id: number
  name: string
  sort_order: number
  field_type: number
  /**
   * Trường do hệ nạp sẵn: `"priority"` = Độ ưu tiên. Rỗng = người dùng tự khai.
   * Chỉ là cái móc để tìm lại trường ấy (tô màu thanh Gantt, biểu đồ Tổng quan)
   * — tên, bộ giá trị và màu vẫn do từng dự án tự đặt.
   */
  system_key: string
  /** Số việc đang gán giá trị của trường — giao diện khóa ô "kiểu trường" khi > 0. */
  value_count: number
  options: WorkLabelOption[]
}

/**
 * Một giá trị nhãn trên task. Chỉ MỘT cột `value_*` có nghĩa, tùy `field_type`
 * của trường; các cột kia rỗng. `value_number` là CHUỖI vì JSON hóa `Decimal`
 * thành số thực là chỗ 1234.5678 hiện ra 1234.5677999999999.
 */
export interface WorkTaskLabelValue {
  field_id: number
  option_id: number | null
  value_text: string
  value_number: string | null
  value_date: string
  value_employee_id: number | null
  value_employee_name: string
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
  /** `WORK_TASK_KIND` — cột mốc chỉ dùng `due_date`, Gantt vẽ hình thoi (B-14). */
  kind: number
  start_date: string
  due_date: string
  sort_order: number
  creator_employee_id: number
  completed_at: string | null
  completed_by: number | null
  created_at: string
  updated_at: string
  assignees: WorkAssignee[]
  labels: WorkTaskLabelValue[]
  subtask_done: number
  subtask_total: number
  comment_count: number
  /** Chỉ có ở `GET /tasks/{id}` — panel chi tiết (D-03). */
  subtasks?: WorkTask[]
}

/**
 * Một mũi tên phụ thuộc trên Gantt (B-15). Cặp `(predecessor, successor)` là
 * duy nhất — máy chủ chặn trùng cặp và chặn vòng lặp (`link_service`).
 */
export interface WorkTaskLink {
  id: number
  list_id: number
  predecessor_id: number
  successor_id: number
  link_type: number
  /** Độ trễ (ngày) cộng vào mốc của việc sau; âm = chồng lấn. Hiện chỉ hiển thị. */
  lag_days: number
}

export interface WorkBoard {
  list: WorkList
  sections: WorkSection[]
  /** CHỈ task cha: việc con không bao giờ thành thẻ trên bảng (C-05). */
  tasks: WorkTask[]
  /**
   * Mũi tên phụ thuộc của cả dự án, đi CHUNG payload bảng để Gantt vẽ thanh và
   * mũi tên trong cùng một nhịp. Bảng và Danh sách không đọc tới.
   */
  links: WorkTaskLink[]
}
