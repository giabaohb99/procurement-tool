import { apiDelete, apiGet, apiPatch, apiPost } from '@/core/api'
import type { ListParams, PaginatedResult } from '@/shared/types/api'
import type {
  LeaveEncashment,
  LeaveEncashmentCreatePayload,
  LeaveEncashmentInboxRow,
  LeaveEncashmentPreview,
  LeaveEncashmentUpdatePayload,
} from '../types/leave-encashment'

/** Tầng API của Phiếu thanh toán nghỉ phép (duoc-CR-719) — chỉ gọi HTTP. Hợp đồng: reports/phase-03-backend.md. */

const BASE = '/api/leave-encashments'

export interface LeaveEncashmentPreviewParams {
  leave_type_id: number
  /** `0` = chính mình. */
  employee_id: number
  balance_year: number
  reason_kind: number
}

export const leaveEncashmentApi = {
  list: (params: ListParams) => apiGet<PaginatedResult<LeaveEncashment>>(BASE, { params }),

  /** Phiếu ĐANG chờ chính tôi ký. Gác bằng đăng nhập, không cần khóa `read`. */
  listToApprove: () =>
    apiGet<{ total: number; items: LeaveEncashmentInboxRow[] }>(`${BASE}/to-approve`),

  /** Số được thanh toán (chỉ đọc). Gác `leave_encashment.create`; xem hộ người khác cần quyền lập hộ. */
  preview: (params: LeaveEncashmentPreviewParams) =>
    apiGet<LeaveEncashmentPreview>(`${BASE}/preview`, { params }),

  get: (id: number) => apiGet<LeaveEncashment>(`${BASE}/${id}`),

  create: (payload: LeaveEncashmentCreatePayload) => apiPost<LeaveEncashment>(BASE, payload),

  update: (id: number, payload: LeaveEncashmentUpdatePayload) =>
    apiPatch<LeaveEncashment>(`${BASE}/${id}`, payload),

  remove: (id: number) => apiDelete<null>(`${BASE}/${id}`),

  submit: (id: number) => apiPost<LeaveEncashment>(`${BASE}/${id}/submit`, {}),

  /** Duyệt THẲNG — chỉ chạy khi chưa có phiên duyệt (công tắc bộ máy duyệt đang tắt). */
  approve: (id: number) => apiPost<LeaveEncashment>(`${BASE}/${id}/approve`, {}),

  reject: (id: number, reason: string) =>
    apiPost<LeaveEncashment>(`${BASE}/${id}/reject`, {}, { params: { reason } }),

  cancel: (id: number, reason: string) =>
    apiPost<LeaveEncashment>(`${BASE}/${id}/cancel`, {}, { params: { reason } }),
}
