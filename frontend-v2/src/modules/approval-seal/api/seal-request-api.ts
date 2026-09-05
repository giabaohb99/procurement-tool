import { apiDelete, apiGet, apiPatch, apiPost } from '@/core/api'
import type { ListParams, PaginatedResult } from '@/shared/types/api'
import type {
  SealApproversResult,
  SealRequest,
  SealRequestPayload,
} from '../types/seal-request'

const BASE_URL = '/api/seal-requests'

export const sealRequestApi = {
  list: (params: ListParams) => apiGet<PaginatedResult<SealRequest>>(BASE_URL, { params }),

  get: (id: number) => apiGet<SealRequest>(`${BASE_URL}/${id}`),

  /** TBP đủ điều kiện duyệt + id người duyệt mặc định (điền sẵn khi tạo mới). */
  listApprovers: () => apiGet<SealApproversResult>(`${BASE_URL}/approvers`),

  /** `submit=true` gửi duyệt luôn; ngược lại lưu nháp. */
  create: (payload: SealRequestPayload, submit: boolean) =>
    apiPost<SealRequest>(BASE_URL, payload, { params: { submit } }),

  update: (id: number, payload: Partial<SealRequestPayload>, submit: boolean) =>
    apiPatch<SealRequest>(`${BASE_URL}/${id}`, payload, { params: { submit } }),

  remove: (id: number) => apiDelete<null>(`${BASE_URL}/${id}`),

  /** Gửi duyệt (backend đòi ≥1 chứng từ đã ký đính kèm). */
  submit: (id: number) => apiPost<SealRequest>(`${BASE_URL}/${id}/submit`, {}),

  // --- Trưởng bộ phận (quyền seal_request.approve) ---
  approve: (id: number) => apiPost<SealRequest>(`${BASE_URL}/${id}/approve`, {}),
  returnForEdit: (id: number, reason: string) =>
    apiPost<SealRequest>(`${BASE_URL}/${id}/return`, { reason }),
  reject: (id: number, reason: string) =>
    apiPost<SealRequest>(`${BASE_URL}/${id}/reject`, { reason }),

  // --- Văn thư (quyền seal_request.write) ---
  complete: (id: number, payload: { note: string }) =>
    apiPost<SealRequest>(`${BASE_URL}/${id}/complete`, payload),
  returnClerk: (id: number, reason: string) =>
    apiPost<SealRequest>(`${BASE_URL}/${id}/return-clerk`, { reason }),
  rejectClerk: (id: number, reason: string) =>
    apiPost<SealRequest>(`${BASE_URL}/${id}/reject-clerk`, { reason }),
}
