/**
 * BỘ MÁY PHÊ DUYỆT DÙNG CHUNG (phase 3, nhóm I).
 *
 * Không thuộc phân hệ nào: cùng một bộ máy chạy cho văn bản, YCMH, ĐMH, khảo
 * sát, YCBG, YCTT. Vì thế mọi thứ ở đây nói bằng `entity` + `entity_id` chứ
 * không nhắc tên một loại chứng từ cụ thể nào.
 *
 * ⚠️ Nhãn tiếng Việt do BACKEND cấp (`*_label`), giao diện không chép cứng —
 * thêm một trạng thái mà quên sửa một trong hai chỗ thì màn hình hiện số thô.
 */

export const INSTANCE_STATUS = {
  running: 1,
  approved: 2,
  rejected: 3,
  returned: 4,
  withdrawn: 5,
  /** Không tìm được người duyệt — phiếu phải hiện ra chứ không được biến mất. */
  blocked: 6,
} as const

export const TASK_STATUS = {
  waiting: 1,
  pending: 2,
  approved: 3,
  rejected: 4,
  /** Tự qua vì trùng người duyệt — KHÁC "đã duyệt", xem `instance_model.py`. */
  skippedDuplicate: 5,
  cancelled: 6,
} as const

/** Việc người duyệt đã bấm — xem `ACTION_LABELS` ở `instance_model.py`. */
export const ACTION = {
  start: 1,
  approve: 2,
  reject: 3,
  return: 4,
  withdraw: 5,
  skipDuplicate: 6,
  reassign: 7,
  comment: 8,
  escalate: 9,
  finish: 10,
} as const

export const NODE_KIND = { approval: 1, cc: 2 } as const
export const MULTI_MODE = { any: 1, all: 2, sequential: 3, quorum: 4 } as const
export const APPROVER_KIND = {
  employee: 1,
  role: 2,
  deptHead: 3,
  levelUp: 4,
  companyRep: 5,
  field: 6,
} as const
/**
 * ⚠️ `escalate` (đẩy lên cấp trên) **ĐÃ BỎ** (CR-114) — backend không chạy nhánh
 * đó nữa và cũng không trả nó về trong danh sách chọn, nên ô «Khi không tìm được
 * người duyệt» tự mất lựa chọn này. Giữ số 2 ở đây để luồng cũ đã khai giá trị
 * đó vẫn đọc ra nhãn thay vì hiện số thô.
 */
export const ON_NO_APPROVER = { fallback: 1, escalate: 2, block: 3 } as const

export interface ApprovalOption {
  value: number
  label: string
}

export interface ApprovalOptions {
  node_kinds: ApprovalOption[]
  flow_roles: ApprovalOption[]
  approver_kinds: ApprovalOption[]
  multi_modes: ApprovalOption[]
  skip_modes: ApprovalOption[]
  on_no_approver: ApprovalOption[]
}

export interface ApprovalNode {
  id: number
  flow_id: number
  seq: number
  branch_key: string
  name: string
  node_kind: number
  node_kind_label: string
  flow_role: number
  flow_role_label: string
  approver_kind: number
  approver_kind_label: string
  approver_ref: string
  approver_names: string
  multi_mode: number
  multi_mode_label: string
  quorum_percent: number
  condition: string
  /** Cột chống mất phiếu — không có thì phiếu không khớp nhánh nào sẽ kẹt. */
  is_default_branch: boolean
  skip_duplicate: number
  skip_duplicate_label: string
  sla_hours: number
  fallback_employee_id: number | null
  fallback_name: string
  on_no_approver: number
  on_no_approver_label: string
}

export interface ApprovalFlow {
  id: number
  entity: string
  code: string
  name: string
  description: string
  /** Tăng mỗi lần sửa. Phiếu đang chạy giữ bản chụp riêng nên không bị ảnh hưởng. */
  version_no: number
  is_active: boolean
  company_id: number | null
  priority: number
  condition: string
  node_count: number
  /**
   * Câu cảnh báo khi có luồng MẶC ĐỊNH khác cùng bật cho loại chứng từ này —
   * chỉ một trong số đó được chọn, các luồng còn lại nằm im. Rỗng = không trùng.
   */
  duplicate_default_warning: string
  nodes?: ApprovalNode[]
}

export interface ApprovalTask {
  id: number
  instance_id: number
  node_seq: number
  node_name: string
  order_no: number
  assignee_employee_id: number
  assignee_name: string
  status: number
  status_label: string
  due_at: string | null
  decided_at: string | null
}

/** Một dòng của hộp việc «Chờ tôi duyệt» — kèm sẵn thông tin phiếu để khỏi gọi thêm. */
export interface MyTask extends ApprovalTask {
  entity: string
  entity_id: number
  entity_code: string
  entity_title: string
  started_by_name: string
  instance_status: number
  /** Có giá trị = đang bấm THAY người khác theo ủy quyền. */
  on_behalf_of_id: number | null
  on_behalf_of_name: string
  delegation_id: number | null
  is_overdue: boolean
}

/**
 * Một dòng của «Đã duyệt gần đây» — MỘT quyết định chính tôi đã bấm.
 *
 * Đọc từ dấu vết chứ không từ bảng việc: dấu vết ghi rõ *đã làm gì* (duyệt /
 * trả lại / từ chối) kèm ý kiến, và ghi đúng tên người BẤM nên người bấm thay
 * theo ủy quyền vẫn thấy phiếu mình đã ký.
 */
export interface MyDecision {
  id: number
  instance_id: number
  entity: string
  entity_id: number
  entity_code: string
  entity_title: string
  node_seq: number
  node_name: string
  action: number
  action_label: string
  comment: string
  decided_at: string
  /** Trạng thái CUỐI của phiếu — "tôi đã duyệt" khác "phiếu đã xong". */
  instance_status: number
  instance_status_label: string
  /** Có giá trị = lúc đó tôi bấm THAY người này theo ủy quyền. */
  on_behalf_of_name: string
}

export interface ApprovalAction {
  id: number
  node_seq: number
  node_name: string
  action: number
  action_label: string
  actor_name: string
  on_behalf_of_name: string
  delegation_id: number | null
  comment: string
  created_at: string
  /** Câu đọc được do backend dựng — bản in trên web và bản xuất không lệch chữ. */
  sentence: string
}

export interface ApprovalInstance {
  id: number
  entity: string
  entity_id: number
  entity_code: string
  entity_title: string
  flow_id: number
  flow_version: number
  flow_name: string
  status: number
  status_label: string
  current_seq: number
  started_by_name: string
  started_at: string | null
  finished_at: string | null
  finish_reason: string
  tasks?: ApprovalTask[]
  actions?: ApprovalAction[]
  steps?: { seq: number; name: string; branch_key: string }[]
}

export interface ApprovalTrail {
  instance: ApprovalInstance
  lines: ApprovalAction[]
  tasks: ApprovalTask[]
}

export interface ApprovalSwitch {
  entity: string
  is_enabled: boolean
  note: string
}

export interface Delegation {
  id: number
  from_employee_id: number
  from_name: string
  to_employee_id: number
  to_name: string
  entity: string
  from_date: string
  to_date: string
  is_active: boolean
  reason: string
}
