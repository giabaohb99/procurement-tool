import { apiDelete, apiGet, apiPatch, apiPost, apiPut } from '@/core/api'
import type { ListParams, PaginatedResult } from '@/shared/types/api'
import type {
  LeavePolicyAssignment,
  LeavePolicyLine,
  PolicyAssignPayload,
  PolicyAssignmentUpdatePayload,
  PolicyBalanceChanges,
  PolicyBulkPayload,
  PolicyBulkResult,
  PolicyPreviewPayload,
  PolicyPreviewResult,
} from '../types/leave-policy'

/**
 * Tầng API của Chính sách nghỉ phép + Phân bổ chính sách (duoc-CR-717) — chỉ gọi HTTP.
 * Danh sách / chi tiết / thêm / sửa / xóa GÓI chính sách đi qua khung CRUD (`leave-policy-crud.tsx`).
 */

const POLICIES = '/api/leave-policies'
const ASSIGNMENTS = '/api/leave-policy-assignments'

export interface PolicyAssignmentWriteResult {
  assignment: LeavePolicyAssignment
  balances: PolicyBalanceChanges
}

export const leavePolicyApi = {
  listLines: (policyId: number) =>
    apiGet<PaginatedResult<LeavePolicyLine>>(`${POLICIES}/${policyId}/lines`),

  /** THAY cả danh sách dòng của gói (trần 50 dòng). Quỹ đã cấp không tự tính lại. */
  replaceLines: (policyId: number, items: LeavePolicyLine[]) =>
    apiPut<PaginatedResult<LeavePolicyLine>>(`${POLICIES}/${policyId}/lines`, {
      items: items.map(({ leave_type_id, annual_days }) => ({ leave_type_id, annual_days })),
    }),

  listAssignments: (params: ListParams) =>
    apiGet<PaginatedResult<LeavePolicyAssignment>>(ASSIGNMENTS, { params }),

  /** Xem trước — KHÔNG ghi gì. Cần `leave_balance.write` (cùng gác với đường ghi). */
  preview: (payload: PolicyPreviewPayload) =>
    apiPost<PolicyPreviewResult>(`${ASSIGNMENTS}/preview`, payload),

  create: (payload: PolicyAssignPayload) =>
    apiPost<PolicyAssignmentWriteResult>(ASSIGNMENTS, payload),

  bulk: (payload: PolicyBulkPayload) => apiPost<PolicyBulkResult>(`${ASSIGNMENTS}/bulk`, payload),

  /** Chỉ sửa được `effective_to` (null = không thời hạn) và `note`. */
  update: (id: number, payload: PolicyAssignmentUpdatePayload) =>
    apiPatch<PolicyAssignmentWriteResult>(`${ASSIGNMENTS}/${id}`, payload),

  remove: (id: number, recalcCurrentYear: boolean) =>
    apiDelete<{ balances: PolicyBalanceChanges }>(`${ASSIGNMENTS}/${id}`, {
      params: { recalc_current_year: recalcCurrentYear },
    }),
}
