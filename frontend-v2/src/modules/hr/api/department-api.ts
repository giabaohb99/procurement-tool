import { apiDelete, apiGet, apiPatch, apiPost, apiPut } from '@/core/api'
import type { ListParams, PaginatedResult } from '@/shared/types/api'
import type { Department, DepartmentCompany, DepartmentCompanyInput } from '../types/department'
import type { DepartmentFormValues } from '../schemas/department-schema'

const BASE_URL = '/api/departments'

/**
 * Danh mục Phòng ban.
 *
 * ⚠️ Endpoint danh sách KHÔNG dùng whitelist `apply_filters` như các module khác:
 * nó nhận một tham số `q` tìm chung theo TÊN PHÒNG BAN hoặc TÊN TRƯỞNG BỘ PHẬN
 * (join sang bảng nhân sự), cộng `is_active`. Đừng gửi `name=` — backend bỏ qua.
 */
export const departmentApi = {
  list: (params: ListParams) => apiGet<PaginatedResult<Department>>(BASE_URL, { params }),

  getById: (id: number) => apiGet<Department>(`${BASE_URL}/${id}`),

  create: (payload: DepartmentFormValues) => apiPost<Department>(BASE_URL, payload),

  update: (id: number, payload: Partial<DepartmentFormValues>) =>
    apiPatch<Department>(`${BASE_URL}/${id}`, payload),

  remove: (id: number) => apiDelete<null>(`${BASE_URL}/${id}`),

  listCompanies: (id: number) => apiGet<DepartmentCompany[]>(`${BASE_URL}/${id}/companies`),

  replaceCompanies: (id: number, items: DepartmentCompanyInput[]) =>
    apiPut<DepartmentCompany[]>(`${BASE_URL}/${id}/companies`, { items }),
}
