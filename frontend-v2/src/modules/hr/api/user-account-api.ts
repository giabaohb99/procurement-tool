import type { AxiosRequestConfig } from 'axios'

import { apiDelete, apiGet, httpClient } from '@/core/api'
import type { SuccessEnvelope } from '@/core/api'
import type { ListParams, PaginatedResult } from '@/shared/types/api'
import type { UserAccount, UserScope } from '../types/user-account'

const BASE_URL = '/api/users'

/**
 * Tài khoản đăng nhập + phạm vi dữ liệu.
 *
 * ⚠️ Danh sách KHÔNG dùng `apply_filters`: tham số là các trường rời rạc
 * (`search`, `department`, `role_id`, `no_role`, `orphan`, `sort`) do
 * `user/service.py` tự xử lý.
 */
export const userAccountApi = {
  list: (params: ListParams) => apiGet<PaginatedResult<UserAccount>>(BASE_URL, { params }),

  getById: (id: number) => apiGet<UserAccount>(`${BASE_URL}/${id}`),

  /** Tra CHÍNH XÁC tài khoản của một nhân sự. Không có thì trả về `null`. */
  findByEmployee: async (employeeId: number) => {
    const res = await apiGet<PaginatedResult<UserAccount>>(BASE_URL, {
      params: { employee_id: employeeId, page_size: 1 },
      // Cờ riêng của http-client: nhân sự chưa có tài khoản là chuyện bình
      // thường, đừng để interceptor bắn toast lỗi.
      _silent: true,
    } as AxiosRequestConfig)
    return res.items[0] ?? null
  },

  assignRoles: (userId: number, roleIds: number[]) =>
    httpClient.put<SuccessEnvelope<null>>(`${BASE_URL}/${userId}/roles`, {
      role_ids: roleIds,
    }),

  setActive: (userId: number, isActive: boolean) =>
    httpClient.put<SuccessEnvelope<null>>(`${BASE_URL}/${userId}/active`, {
      is_active: isActive,
    }),

  remove: (userId: number) => apiDelete<null>(`${BASE_URL}/${userId}`),

  getScope: (userId: number, roleId: number) =>
    apiGet<Partial<UserScope>>(`${BASE_URL}/${userId}/roles/${roleId}/scope`),

  setScope: (userId: number, roleId: number, scope: UserScope) =>
    httpClient.put<SuccessEnvelope<null>>(
      `${BASE_URL}/${userId}/roles/${roleId}/scope`,
      scope,
    ),
}
