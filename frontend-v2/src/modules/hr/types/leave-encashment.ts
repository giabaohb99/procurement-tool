import type { ApprovalFlowStrip, LeaveApprovalTask } from './leave'

/**
 * Kiểu dữ liệu PHIẾU THANH TOÁN NGHỈ PHÉP (duoc-CR-719, kiểu Leave Encashment của ERPNext).
 *
 * Phiếu = "đổi N ngày phép chưa nghỉ ra tiền" — cuối năm (phép dư) hoặc khi nghỉ việc. Phiếu CHỈ ghi số ngày;
 * duyệt xong backend trừ quỹ (`encashed_days`) và sinh một YCTT Nháp ở Tài chính để kế toán nhập tiền.
 *
 * ⚠️ Bộ mã phải khớp `LeaveEncashmentStatus` / `LeaveEncashmentReason` ở `backend/app/modules/leave/constants.py`
 * (bộ mã SỐ của nghỉ phép gõ tay, `gen_status_ts.py` chỉ sinh bộ mã chuỗi). Trạng thái cố ý TRÙNG số với đơn nghỉ
 * (1..6) để dùng chung `LeaveStatusBadge`.
 */

export const LEAVE_ENCASHMENT_STATUS = {
  DRAFT: 1,
  PENDING: 2,
  APPROVED: 3,
  REJECTED: 4,
  RETURNED: 5,
  CANCELLED: 6,
} as const

export const LEAVE_ENCASHMENT_STATUS_LABELS: Record<number, string> = {
  [LEAVE_ENCASHMENT_STATUS.DRAFT]: 'Nháp',
  [LEAVE_ENCASHMENT_STATUS.PENDING]: 'Chờ duyệt',
  [LEAVE_ENCASHMENT_STATUS.APPROVED]: 'Đã duyệt',
  [LEAVE_ENCASHMENT_STATUS.REJECTED]: 'Từ chối',
  [LEAVE_ENCASHMENT_STATUS.RETURNED]: 'Trả về chỉnh sửa',
  [LEAVE_ENCASHMENT_STATUS.CANCELLED]: 'Đã hủy',
}

/** Lý do thanh toán — D5: nghỉ việc bỏ qua hai trần và tính cả phần mang sang. */
export const LEAVE_ENCASHMENT_REASON = {
  YEAR_END: 1,
  RESIGNATION: 2,
} as const

export const LEAVE_ENCASHMENT_REASON_LABELS: Record<number, string> = {
  [LEAVE_ENCASHMENT_REASON.YEAR_END]: 'Phép dư cuối năm',
  [LEAVE_ENCASHMENT_REASON.RESIGNATION]: 'Nghỉ việc',
}

/** Sửa được khi còn Nháp hoặc bị Trả về — khớp `ENCASH_EDITABLE_STATUSES` của backend. */
export const EDITABLE_LEAVE_ENCASHMENT_STATUSES: number[] = [
  LEAVE_ENCASHMENT_STATUS.DRAFT,
  LEAVE_ENCASHMENT_STATUS.RETURNED,
]

export const ENCASHMENT_NOTE_MAX = 1000
export const ENCASHMENT_DECISION_REASON_MAX = 500

/** Mã trạng thái YCTT (bộ mã chuỗi thu mua, QĐ-9) mà phiếu đọc về. Rỗng = chưa có YCTT. */
export type EncashmentPaymentStatus = '' | 'draft' | 'submitted' | 'approved' | 'paid' | 'cancelled'

/**
 * Khối `payment` của chi tiết phiếu. `total` = null khi người xem KHÔNG được thấy số tiền (người duyệt Nhân sự
 * không có quyền YCTT) — màn hình chỉ vẽ số khi khác null, không tự tính, không gọi API YCTT.
 */
export interface EncashmentPayment {
  id: number
  code: string
  status: Exclude<EncashmentPaymentStatus, ''>
  status_label: string
  total: number | null
}

/** `type` chứ không `interface` — cùng lý do với `LeaveType` (khuôn bảng cần chỉ mục ngầm). */
export type LeaveEncashment = {
  id: number
  /** `TTP#####`. */
  code: string
  company_id: number
  department_id: number
  department_name: string
  employee_id: number
  employee_name: string
  employee_code: string
  leave_type_id: number
  leave_type_name: string
  balance_year: number
  reason_kind: number
  reason_kind_label: string
  encashment_date: string | null
  days: number
  /** Số dùng được / số được thanh toán chụp lúc gửi duyệt. */
  balance_snapshot: number
  encashable_snapshot: number
  note: string
  status: number
  status_label: string
  /** `0` = không có phiên duyệt nào đang chạy (duyệt thẳng). */
  approval_instance_id: number
  decided_at: string | null
  decision_note: string
  /** `0` = chưa sinh YCTT. */
  payment_request_id: number
  payment_status: EncashmentPaymentStatus
  payment_status_label: string
  created_by: number
  created_at: string
  updated_at: string
  /** Bốn trường dưới chỉ có ở `GET /{id}`. */
  created_by_name?: string
  has_running_approval?: boolean
  payment?: EncashmentPayment | null
  /** Khác rỗng = nút Hủy phải tắt (YCTT đã gửi duyệt / đã duyệt / đã chi). */
  cancel_blocked_reason?: string
}

/** Dòng của `GET /to-approve` — phiếu kèm việc duyệt của tôi và luồng. */
export type LeaveEncashmentInboxRow = LeaveEncashment & {
  task: LeaveApprovalTask
  flow?: ApprovalFlowStrip | null
}

/** `GET /preview` — số liệu để điền form, chỉ đọc. `cap_remaining = null` = không trần năm. */
export interface LeaveEncashmentPreview {
  has_balance: boolean
  available: number
  unused_carried: number
  already_encashed: number
  non_encashable_days: number
  max_encashable_days: number
  cap_remaining: number | null
  encashable: number
  employee_id: number
  leave_type_id: number
  balance_year: number
  reason_kind: number
  reason_kind_label: string
}

export interface LeaveEncashmentCreatePayload {
  /** `0` / vắng = chính mình. */
  employee_id?: number
  leave_type_id: number
  balance_year?: number
  reason_kind: number
  encashment_date?: string | null
  /** `null` = lấy đúng số được phép thanh toán lúc lập. */
  days?: number | null
  note?: string
}

/** Sửa phiếu Nháp / Trả về: không đổi người, loại nghỉ, năm quỹ. */
export interface LeaveEncashmentUpdatePayload {
  reason_kind?: number
  encashment_date?: string | null
  days?: number | null
  note?: string
}

export type LeaveEncashmentAction = 'submit' | 'approve' | 'reject' | 'cancel'

export interface LeaveEncashmentActionAvailability {
  edit: boolean
  remove: boolean
  submit: boolean
  /** Duyệt / từ chối THẲNG — chỉ khi chưa có phiên duyệt chạy. */
  directDecision: boolean
  /** Ba nút của bộ máy (duyệt / trả về / từ chối) — khi đang có phiên duyệt chạy. */
  engineDecision: boolean
  cancel: boolean
}

export interface LeaveEncashmentPermissionFlags {
  write: boolean
  delete: boolean
  approve: boolean
  cancel: boolean
  /** Phiếu là của chính người xem (nhân sự nhận thanh toán) — tự duyệt luôn bị chặn nên không bày nút Duyệt thẳng. */
  isOwnRequest?: boolean
}

/**
 * Nút nào được hiện trên trang chi tiết — hàm thuần để test, không đọc quyền ở đây.
 *
 * Hủy: backend nhận Chờ duyệt / Trả về / Đã duyệt (Nháp thì Xóa). Phiếu Đã duyệt mà YCTT đã gửi duyệt / đã duyệt /
 * đã chi thì backend trả `cancel_blocked_reason` khác rỗng — không bày nút mời bấm rồi ăn 400.
 */
export function getLeaveEncashmentActions(
  request:
    | Pick<LeaveEncashment, 'status' | 'approval_instance_id' | 'cancel_blocked_reason'>
    | undefined,
  can: LeaveEncashmentPermissionFlags,
): LeaveEncashmentActionAvailability {
  const none: LeaveEncashmentActionAvailability = {
    edit: false,
    remove: false,
    submit: false,
    directDecision: false,
    engineDecision: false,
    cancel: false,
  }
  if (!request) return none
  const editable = EDITABLE_LEAVE_ENCASHMENT_STATUSES.includes(request.status)
  const pending = request.status === LEAVE_ENCASHMENT_STATUS.PENDING
  const cancellable =
    pending ||
    request.status === LEAVE_ENCASHMENT_STATUS.RETURNED ||
    request.status === LEAVE_ENCASHMENT_STATUS.APPROVED
  return {
    edit: editable && can.write,
    remove: request.status === LEAVE_ENCASHMENT_STATUS.DRAFT && can.delete,
    submit: editable && can.write,
    directDecision: pending && request.approval_instance_id === 0 && can.approve && !can.isOwnRequest,
    engineDecision: pending && request.approval_instance_id > 0,
    cancel: cancellable && can.cancel && !(request.cancel_blocked_reason ?? '').trim(),
  }
}

/** Kế toán từ chối YCTT (D7a): phiếu giữ Đã duyệt, Nhân sự hủy phiếu để trả lại ngày. */
export function isPayoutRejected(
  request: Pick<LeaveEncashment, 'status' | 'payment_status'> | undefined,
): boolean {
  return request?.status === LEAVE_ENCASHMENT_STATUS.APPROVED && request.payment_status === 'cancelled'
}

/** Năm quỹ chọn được (D9): năm nay hoặc năm trước. */
export function encashmentYearOptions(today: Date): number[] {
  const year = today.getFullYear()
  return [year, year - 1]
}

/** Số ngày hợp lệ: lớn hơn 0, bước 0,5, không vượt `max` (khi biết). Trả câu lỗi hoặc rỗng. */
export function validateEncashmentDays(days: number, max: number | null): string {
  if (!Number.isFinite(days) || days <= 0) return 'Số ngày phải lớn hơn 0.'
  if (Math.abs(days * 2 - Math.round(days * 2)) > 1e-9) return 'Số ngày đi theo bước 0,5 ngày.'
  if (max !== null && days > max + 1e-9) return `Chỉ được thanh toán tối đa ${formatEncashDays(max)} ngày.`
  return ''
}

/** `1.5` → `1,5` (dấu phẩy thập phân kiểu Việt), số nguyên giữ nguyên. */
export function formatEncashDays(value: number): string {
  const rounded = Math.round((Number(value) || 0) * 100) / 100
  return String(rounded).replace('.', ',')
}
