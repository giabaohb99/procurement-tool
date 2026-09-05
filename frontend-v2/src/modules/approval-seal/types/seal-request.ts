/**
 * Kiểu & bộ mã của phân hệ DUYỆT DẤU (yêu cầu đóng dấu).
 *
 * Cột `status` backend lưu SMALLINT (rule R2) và trả kèm số + nhãn. Bản đối chiếu
 * nhãn ở đây phải KHỚP `SEAL_STATUS_LABELS` bên backend (`model.py`).
 */

// --- Trạng thái phiếu -----------------------------------------------------
export const SEAL_STATUS = {
  draft: 1, // Nháp
  pending: 2, // Chờ duyệt (TBP)
  approved: 3, // Đã duyệt — chờ Văn thư đóng dấu
  completed: 4, // Hoàn thành
  rejected: 5, // Từ chối
  cancelled: 6, // Đã hủy
  returned: 7, // Yêu cầu chỉnh sửa
} as const
export type SealStatus = (typeof SEAL_STATUS)[keyof typeof SEAL_STATUS]

export const SEAL_STATUS_LABELS: Record<number, string> = {
  [SEAL_STATUS.draft]: 'Nháp',
  [SEAL_STATUS.pending]: 'Chờ duyệt',
  [SEAL_STATUS.approved]: 'Đã duyệt',
  [SEAL_STATUS.completed]: 'Hoàn thành',
  [SEAL_STATUS.rejected]: 'Từ chối',
  [SEAL_STATUS.cancelled]: 'Đã hủy',
  [SEAL_STATUS.returned]: 'Yêu cầu chỉnh sửa',
}

/**
 * Tông màu badge dạng "pill" (gray/warn/ok/err/info). Màu cụ thể của mỗi tông
 * khai ở `components/status-pill.tsx` — đây chỉ là bản đồ trạng thái → tông.
 */
export type BadgeTone = 'gray' | 'warn' | 'ok' | 'err' | 'info'

export const SEAL_STATUS_BADGE: Record<number, BadgeTone> = {
  [SEAL_STATUS.draft]: 'gray', // Nháp
  [SEAL_STATUS.pending]: 'warn', // Chờ duyệt
  [SEAL_STATUS.approved]: 'info', // Đã duyệt (chờ đóng dấu)
  [SEAL_STATUS.completed]: 'ok', // Hoàn thành
  [SEAL_STATUS.rejected]: 'err', // Từ chối
  [SEAL_STATUS.cancelled]: 'gray', // Đã hủy — kết thúc, trung tính
  [SEAL_STATUS.returned]: 'warn', // Yêu cầu chỉnh sửa (bị trả lại)
}

/** Chỉ sửa được khi phiếu còn nháp hoặc bị trả về (khớp EDITABLE_STATUSES ở backend). */
export const EDITABLE_SEAL_STATUSES = new Set<number>([SEAL_STATUS.draft, SEAL_STATUS.returned])

// --- Bản ghi phiếu (khớp SealRequestResponse) -----------------------------
export interface SealRequest {
  id: number
  code: string
  status: number
  status_label: string
  purpose: string
  title: string
  seal_type_id: number
  seal_type_name: string
  company_id: number
  company_name: string
  company_tax_code: string
  department_id: number
  copies: number
  first_approver_id: number
  approver_name: string
  requester: string
  requester_id: number
  requester_email: string
  requester_phone: string
  requester_role: string
  signed_doc_count: number
  note: string
  created_at: string | null
  /** True khi phiếu đang chạy một phiên duyệt nhiều bước (bộ máy `ApprovalSwitch`). */
  approval_running: boolean
}

/** Payload tạo/sửa phiếu — form gửi đúng bộ trường backend nhận. */
export interface SealRequestPayload {
  purpose: string
  title?: string
  seal_type_id: number
  company_id: number
  department_id?: number
  copies?: number
  first_approver_id?: number
  note?: string
}
