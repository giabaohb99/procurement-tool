import { apiDelete, apiGet, apiPatch, apiPost } from '@/core/api'
import type { ListParams, PaginatedResult } from '@/shared/types/api'
import type { Supplier } from '../types/supplier'
import type { SupplierFormValues } from '../schemas/supplier-schema'

const BASE_URL = '/api/suppliers'

/**
 * Tầng API của module: CHỈ gọi HTTP, không chứa logic React.
 * Nhờ tách vậy mà hook (`hooks/`) lo cache còn file này lo endpoint — test và
 * đổi endpoint đều gọn.
 */
export const supplierApi = {
  list: (params: ListParams) =>
    apiGet<PaginatedResult<Supplier>>(BASE_URL, { params }),

  getById: (id: number) => apiGet<Supplier>(`${BASE_URL}/${id}`),

  create: (payload: SupplierFormValues) => apiPost<Supplier>(BASE_URL, payload),

  update: (id: number, payload: Partial<SupplierFormValues>) =>
    apiPatch<Supplier>(`${BASE_URL}/${id}`, payload),

  remove: (id: number) => apiDelete<null>(`${BASE_URL}/${id}`),
}
