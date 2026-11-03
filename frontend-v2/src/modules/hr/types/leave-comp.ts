import type { ApprovalFlowStrip, LeaveApprovalTask } from './leave'

/**
 * Kiểu dữ liệu PHIẾU XIN NGHỈ BÙ (duoc-CR-715 phase C).
 *
 * Phiếu nghỉ bù = "tôi đã đi làm vào ngày nghỉ X, xin cộng Y ngày vào quỹ phép". Được duyệt thì
 * backend cộng `comp_days` vào quỹ của loại nghỉ bật cờ «Loại nhận ngày nghỉ bù».
 *
 * ⚠️ Bộ mã trạng thái phải khớp `LeaveCompStatus` ở `backend/app/modules/leave/constants.py`.
 * Cố ý TRÙNG số với `LEAVE_STATUS` của đơn nghỉ phép (1..6) nên huy hiệu và màu dùng chung
 * `LeaveStatusBadge`; khai bộ riêng để đổi một bên không kéo bên kia.
 */

export const LEAVE_COMP_STATUS = {
  DRAFT: 1,
  PENDING: 2,
  APPROVED: 3,
  REJECTED: 4,
  RETURNED: 5,
  CANCELLED: 6,
} as const

export const LEAVE_COMP_STATUS_LABELS: Record<number, string> = {
  [LEAVE_COMP_STATUS.DRAFT]: 'Nháp',
  [LEAVE_COMP_STATUS.PENDING]: 'Chờ duyệt',
  [LEAVE_COMP_STATUS.APPROVED]: 'Đã duyệt',
  [LEAVE_COMP_STATUS.REJECTED]: 'Từ chối',
  [LEAVE_COMP_STATUS.RETURNED]: 'Trả về chỉnh sửa',
  [LEAVE_COMP_STATUS.CANCELLED]: 'Đã hủy',
}

/** Sửa được khi còn Nháp hoặc bị Trả về — khớp backend. */
export const EDITABLE_LEAVE_COMP_STATUSES: number[] = [
  LEAVE_COMP_STATUS.DRAFT,
  LEAVE_COMP_STATUS.RETURNED,
]

/** Số ngày nghỉ bù hợp lệ: nửa ngày hoặc cả ngày. */
export const LEAVE_COMP_DAY_OPTIONS = [0.5, 1] as const

export const COMP_REASON_MAX = 1000
export const COMP_DECISION_REASON_MAX = 500

/** `type` chứ không `interface` — cùng lý do với `LeaveType` (khuôn CRUD cần chỉ mục ngầm). */
export type LeaveCompRequest = {
  id: number
  code: string
  company_id: number
  department_id: number
  department_name: string
  employee_id: number
  employee_name: string
  employee_code: string
  /** Ngày đi làm bù, `yyyy-mm-dd`. */
  work_date: string
  /** 0.5 hoặc 1. */
  days: number
  reason: string
  status: number
  status_label: string
  /** `0` = không có phiên duyệt nào đang chạy (duyệt thẳng). */
  approval_instance_id: number
  decided_at: string | null
  decision_note: string
  created_by: number
  created_at: string
  updated_at: string
  /** Chỉ có ở `GET /{id}`. */
  created_by_name?: string
  has_running_approval?: boolean
}

/** Dòng của `GET /to-approve` — phiếu kèm việc duyệt của tôi và luồng. */
export type LeaveCompInboxRow = LeaveCompRequest & {
  task: LeaveApprovalTask
  flow?: ApprovalFlowStrip | null
}

export interface LeaveCompPayload {
  /** `0` / vắng = chính mình. */
  employee_id?: number
  work_date?: string
  days?: number
  reason?: string
}

export type LeaveCompAction = 'submit' | 'approve' | 'reject' | 'cancel'

/** Các nút nào được phép hiện trên trang chi tiết — hàm thuần để test, không đọc quyền ở đây. */
export interface LeaveCompActionAvailability {
  edit: boolean
  remove: boolean
  submit: boolean
  /** Duyệt / từ chối THẲNG — chỉ khi chưa có phiên duyệt chạy. */
  directDecision: boolean
  /** Ba nút của bộ máy (duyệt / trả về / từ chối) — khi đang có phiên duyệt chạy. */
  engineDecision: boolean
  cancel: boolean
}

export interface LeaveCompPermissionFlags {
  write: boolean
  delete: boolean
  approve: boolean
  cancel: boolean
}

export function getLeaveCompActions(
  request: Pick<LeaveCompRequest, 'status' | 'approval_instance_id'> | undefined,
  can: LeaveCompPermissionFlags,
): LeaveCompActionAvailability {
  const none: LeaveCompActionAvailability = {
    edit: false,
    remove: false,
    submit: false,
    directDecision: false,
    engineDecision: false,
    cancel: false,
  }
  if (!request) return none
  const editable = EDITABLE_LEAVE_COMP_STATUSES.includes(request.status)
  const pending = request.status === LEAVE_COMP_STATUS.PENDING
  return {
    edit: editable && can.write,
    remove: request.status === LEAVE_COMP_STATUS.DRAFT && can.delete,
    submit: editable && can.write,
    //  ⚠️ Đơn đang chạy trong luồng thì backend chặn duyệt thẳng — không bày nút mời bấm rồi ăn lỗi.
    directDecision: pending && request.approval_instance_id === 0 && can.approve,
    engineDecision: pending && request.approval_instance_id > 0,
    cancel: (pending || request.status === LEAVE_COMP_STATUS.APPROVED) && can.cancel,
  }
}
