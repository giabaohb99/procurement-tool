import { apiDelete, apiGet, apiPatch, apiPost, httpClient } from '@/core/api'
import type { SuccessEnvelope } from '@/core/api'
import type { PermissionMeta, Role, RolePermissionRow } from '../types/role'

const BASE_URL = '/api/roles'

/**
 * Vai trò + ma trận quyền.
 *
 * ⚠️ `GET /api/roles` trả MẢNG THÔ, không phải `{ total, items }` như các danh
 * mục khác — backend cố ý để frontend tự lọc/sắp xếp tại chỗ (số vai trò nhỏ).
 */
export const roleApi = {
  list: () => apiGet<Role[]>(BASE_URL),

  meta: () => apiGet<PermissionMeta>(`${BASE_URL}/meta`),

  create: (payload: { code: string; name: string; description?: string }) =>
    apiPost<Role>(BASE_URL, payload),

  update: (id: number, payload: { name?: string; description?: string }) =>
    apiPatch<Role>(`${BASE_URL}/${id}`, payload),

  remove: (id: number) => apiDelete<null>(`${BASE_URL}/${id}`),

  getPermissions: (roleId: number) =>
    apiGet<RolePermissionRow[]>(`${BASE_URL}/${roleId}/permissions`),

  /**
   * Ghi đè TOÀN BỘ ma trận quyền của vai trò — dòng không gửi lên coi như bị xóa.
   * `apiPut` chưa có trong `@/core/api` nên dùng httpClient trực tiếp.
   */
  setPermissions: (roleId: number, permissions: RolePermissionRow[]) =>
    httpClient.put<SuccessEnvelope<null>>(`${BASE_URL}/${roleId}/permissions`, {
      permissions,
    }),
}
