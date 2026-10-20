import { apiGet, apiPost, httpClient } from '@/core/api'
import type { SuccessEnvelope } from '@/core/api'
import type { ApplyPositionRolesResult, JobPositionRoleBundle } from '../types/job-position-role'

const base = (positionId: number) => `/api/job-positions/${positionId}/roles`

/** Gói quyền mặc định theo chức vụ (duoc-CR-653). Gác bằng quyền Vai trò (`role.read/write`). */
export const jobPositionRoleApi = {
  get: (positionId: number) => apiGet<JobPositionRoleBundle>(base(positionId)),

  /** Ghi đè cả gói. KHÔNG đụng tài khoản nào — muốn áp cho người đang giữ phải gọi `apply`. */
  save: async (positionId: number, roleIds: number[]) => {
    const res = await httpClient.put<SuccessEnvelope<JobPositionRoleBundle>>(base(positionId), {
      role_ids: roleIds,
    })
    return res.data.data
  },

  apply: (positionId: number) => apiPost<ApplyPositionRolesResult>(`${base(positionId)}/apply`),
}
