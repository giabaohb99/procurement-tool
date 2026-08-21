import { apiDelete, apiGet, apiPatch, apiPost } from '@/core/api'
import type { ListParams, PaginatedResult } from '@/shared/types/api'
import type { Contract } from '../types/contract'

const BASE_URL = '/api/contracts'

/**
 * Hợp đồng — danh mục Hợp đồng mua bán / nguyên tắc / dịch vụ (Đ-04).
 *
 * Whitelist lọc của backend (`FILTERABLE`): code · party_type · party_code ·
 * party_name · status · contract_type · title · end_date. Ngoài ra controller tự
 * đọc `signed` và `expiry`.
 */
export const contractApi = {
  list: (params: ListParams) => apiGet<PaginatedResult<Contract>>(BASE_URL, { params }),

  getById: (id: number) => apiGet<Contract>(`${BASE_URL}/${id}`),

  create: (data: Partial<Contract>) => apiPost<Contract>(BASE_URL, data),

  update: (id: number, data: Partial<Contract>) => apiPatch<Contract>(`${BASE_URL}/${id}`, data),

  delete: (id: number) => apiDelete<void>(`${BASE_URL}/${id}`),

  bulkDelete: (ids: number[]) =>
    apiDelete<void>(BASE_URL, { params: { ids: ids.join(',') } }),
}
