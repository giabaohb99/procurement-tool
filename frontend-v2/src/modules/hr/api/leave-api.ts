import { apiDelete, apiGet, apiPatch, apiPost } from '@/core/api'
import type { ListParams, PaginatedResult } from '@/shared/types/api'
import type {
  ApprovalFlowStrip,
  Holiday,
  LeaveBalance,
  LeaveBalanceHint,
  LeaveInboxRow,
  LeaveRequest,
  LeaveType,
  SeniorityTier,
} from '../types/leave'

/** Tầng API của phân hệ Nghỉ phép — chỉ gọi HTTP, không chứa logic React. */

const REQUESTS = '/api/leave-requests'
const INBOX = '/api/leave-requests/inbox'
const BALANCES = '/api/leave-balances'
const TYPES = '/api/leave-types'
const TIERS = '/api/leave-seniority-tiers'
const HOLIDAYS = '/api/holidays'
//  Bộ máy duyệt dùng chung — nghỉ phép gọi thẳng vào đây để duyệt NGAY trong màn
//  của mình, không đẩy người dùng sang màn Phê duyệt (CR-260).
const APPROVALS = '/api/approvals'
const APPROVAL_STEPS = `${APPROVALS}/steps`

export interface LeaveRequestPayload {
  employee_id?: number
  leave_type_id: number
  from_date: string
  to_date: string
  from_session?: number
  to_session?: number
  unit?: number
  /** `0` = để backend tự tính. Khác 0 là người dùng sửa đè. */
  total_days?: number
  reason?: string
  contact_phone?: string
  contact_address?: string
  handovers?: { employee_id: number; content?: string }[]
}

export const leaveApi = {
  // ── Đơn nghỉ phép ───────────────────────────────────────────────────────────
  listRequests: (params: ListParams) =>
    apiGet<PaginatedResult<LeaveRequest>>(REQUESTS, { params }),

  getRequest: (id: number) => apiGet<LeaveRequest>(`${REQUESTS}/${id}`),

  createRequest: (payload: LeaveRequestPayload) =>
    apiPost<LeaveRequest>(REQUESTS, payload),

  updateRequest: (id: number, payload: Partial<LeaveRequestPayload>) =>
    apiPatch<LeaveRequest>(`${REQUESTS}/${id}`, payload),

  removeRequest: (id: number) => apiDelete<null>(`${REQUESTS}/${id}`),

  submitRequest: (id: number) => apiPost<LeaveRequest>(`${REQUESTS}/${id}/submit`, {}),

  /** Duyệt THẲNG — chỉ dùng khi môi trường chưa khai luồng nhiều bước. */
  approveRequest: (id: number) => apiPost<LeaveRequest>(`${REQUESTS}/${id}/approve`, {}),

  rejectRequest: (id: number, reason: string) =>
    apiPost<LeaveRequest>(`${REQUESTS}/${id}/reject`, {}, { params: { reason } }),

  cancelRequest: (id: number, reason: string) =>
    apiPost<LeaveRequest>(`${REQUESTS}/${id}/cancel`, {}, { params: { reason } }),

  /** Số ngày GỢI Ý cho khoảng đang chọn — form gọi mỗi lần đổi ngày. */
  estimateDays: (params: {
    from_date: string
    to_date: string
    leave_type_id?: number
    from_session?: number
    to_session?: number
    employee_id?: number
  }) => apiGet<{ total_days: number }>(`${REQUESTS}/tools/estimate-days`, { params }),

  /**
   * Số phép còn lại — ràng buộc §6.1: form phải hiện con số này lúc nộp.
   * Gác bằng `leave_request.read` chứ không `leave_balance.read`, xem backend.
   */
  balanceHint: (params: { leave_type_id: number; year?: number; employee_id?: number }) =>
    apiGet<LeaveBalanceHint>(`${REQUESTS}/tools/my-balance`, { params }),

  // ── Quỹ phép ────────────────────────────────────────────────────────────────
  listBalances: (params: ListParams) =>
    apiGet<PaginatedResult<LeaveBalance>>(BALANCES, { params }),

  balanceSummary: (params: { employee_id?: number; year?: number }) =>
    apiGet<{
      employee_id: number
      employee_name: string
      year: number
      items: LeaveBalance[]
      total_remaining: number
    }>(`${BALANCES}/tools/summary`, { params }),

  /** Chỉnh tay — ghi ĐÈ `adjusted_days`, bắt buộc có lý do. */
  adjustBalance: (id: number, payload: { adjusted_days: number; note: string }) =>
    apiPatch<LeaveBalance>(`${BALANCES}/${id}/adjust`, payload),

  allocate: (payload: { year: number; leave_type_ids?: number[]; employee_ids?: number[] }) =>
    apiPost<{
      year: number
      employee_count: number
      created: number
      missing_hire_date: string[]
      missing_hire_date_count: number
    }>(`${BALANCES}/allocate`, payload),

  // ── Danh mục nền ────────────────────────────────────────────────────────────
  listTypes: (params: ListParams = {}) =>
    apiGet<PaginatedResult<LeaveType>>(TYPES, { params }),

  listTiers: (leaveTypeId: number) =>
    apiGet<{ total: number; items: SeniorityTier[] }>(TIERS, {
      params: { leave_type_id: leaveTypeId },
    }),

  createTier: (payload: Omit<SeniorityTier, 'id'>) => apiPost<SeniorityTier>(TIERS, payload),

  updateTier: (id: number, payload: Partial<Omit<SeniorityTier, 'id' | 'leave_type_id'>>) =>
    apiPatch<SeniorityTier>(`${TIERS}/${id}`, payload),

  removeTier: (id: number) => apiDelete<null>(`${TIERS}/${id}`),

  listHolidays: (params: ListParams = {}) =>
    apiGet<PaginatedResult<Holiday>>(HOLIDAYS, { params }),

  // ── Hộp việc duyệt (CR-260) ─────────────────────────────────────────────────
  /**
   * Đơn ĐANG chờ chính tôi ký. Backend ghép sẵn tờ đơn + việc + luồng, nên một
   * lượt gọi là đủ dựng cả tab — xem `leave/inbox_controller.py`.
   */
  listToApprove: () => apiGet<{ total: number; items: LeaveInboxRow[] }>(`${INBOX}/to-approve`),

  /** Đơn chính tôi vừa quyết định gần đây. */
  listHandled: (params: { days?: number; limit?: number } = {}) =>
    apiGet<{ total: number; items: LeaveInboxRow[] }>(`${INBOX}/handled`, { params }),

  /**
   * Luồng duyệt của NHIỀU đơn một lượt, cho cột «Luồng duyệt» ở bảng danh sách.
   * Khóa trả về là `entity_id` dạng chuỗi. Đơn chưa vào bộ máy thì KHÔNG có khóa.
   */
  flowStrips: (ids: number[]) =>
    apiGet<Record<string, ApprovalFlowStrip>>(APPROVAL_STEPS, {
      params: { entity: 'leave_request', ids: ids.join(',') },
    }),

  // ── Thao tác duyệt qua BỘ MÁY (khác `approveRequest` là duyệt thẳng) ─────────
  approveInstance: (instanceId: number, comment = '') =>
    apiPost<unknown>(`${APPROVALS}/${instanceId}/approve`, { comment, subject: {} }),

  rejectInstance: (instanceId: number, reason: string) =>
    apiPost<unknown>(`${APPROVALS}/${instanceId}/reject`, { reason }),

  returnInstance: (instanceId: number, reason: string) =>
    apiPost<unknown>(`${APPROVALS}/${instanceId}/return`, { reason, subject: {} }),
}
