import { apiDelete, apiGet, apiPatch, apiPost } from '@/core/api'
import type { ListParams, PaginatedResult } from '@/shared/types/api'
import type {
  LeaveCompInboxRow,
  LeaveCompPayload,
  LeaveCompRequest,
} from '../types/leave-comp'

/** Tầng API của Phiếu xin nghỉ bù (duoc-CR-715 phase C) — chỉ gọi HTTP. */

const BASE = '/api/leave-comp-requests'

export const leaveCompApi = {
  list: (params: ListParams) => apiGet<PaginatedResult<LeaveCompRequest>>(BASE, { params }),

  /** Phiếu ĐANG chờ chính tôi ký. Gác bằng đăng nhập, không cần khóa `read`. */
  listToApprove: () => apiGet<{ total: number; items: LeaveCompInboxRow[] }>(`${BASE}/to-approve`),

  get: (id: number) => apiGet<LeaveCompRequest>(`${BASE}/${id}`),

  create: (payload: LeaveCompPayload) => apiPost<LeaveCompRequest>(BASE, payload),

  update: (id: number, payload: LeaveCompPayload) =>
    apiPatch<LeaveCompRequest>(`${BASE}/${id}`, payload),

  remove: (id: number) => apiDelete<null>(`${BASE}/${id}`),

  submit: (id: number) => apiPost<LeaveCompRequest>(`${BASE}/${id}/submit`, {}),

  /** Duyệt THẲNG — chỉ chạy khi chưa có phiên duyệt (công tắc bộ máy duyệt đang tắt). */
  approve: (id: number) => apiPost<LeaveCompRequest>(`${BASE}/${id}/approve`, {}),

  reject: (id: number, reason: string) =>
    apiPost<LeaveCompRequest>(`${BASE}/${id}/reject`, {}, { params: { reason } }),

  cancel: (id: number, reason: string) =>
    apiPost<LeaveCompRequest>(`${BASE}/${id}/cancel`, {}, { params: { reason } }),
}
