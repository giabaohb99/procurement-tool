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

  /**
   * Gán vai trò. `confirmSelfAdminRemoval` = đã hỏi và người dùng đồng ý TỰ bỏ vai
   * trò Quản trị hệ thống của chính mình (bao-CR-523) — thiếu cờ thì backend trả
   * 409 kèm câu hỏi. Cờ chỉ gửi khi bật để thân request thường không đổi.
   *
   * `_silent`: hook tự báo lỗi — 409 là câu HỎI, không được bắn toast đỏ.
   */
  assignRoles: (userId: number, roleIds: number[], confirmSelfAdminRemoval = false) =>
    httpClient.put<SuccessEnvelope<null>>(
      `${BASE_URL}/${userId}/roles`,
      {
        role_ids: roleIds,
        ...(confirmSelfAdminRemoval ? { confirm_self_admin_removal: true } : {}),
      },
      { _silent: true } as AxiosRequestConfig,
    ),

  setActive: (userId: number, isActive: boolean) =>
    httpClient.put<SuccessEnvelope<null>>(`${BASE_URL}/${userId}/active`, {
      is_active: isActive,
    }),

  /**
   * Quản trị bật/tắt hộ email thông báo cho một tài khoản (bao-CR-349).
   * Backend đòi `user.write` và có ghi nhật ký thao tác.
   */
  setNotifyEmail: (userId: number, notifyEmail: boolean) =>
    httpClient.put<SuccessEnvelope<null>>(`${BASE_URL}/${userId}/notify-email`, {
      notify_email: notifyEmail,
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
