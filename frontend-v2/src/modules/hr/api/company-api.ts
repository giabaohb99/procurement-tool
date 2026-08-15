import { apiDelete, apiGet, apiPatch, apiPost } from '@/core/api'
import type { ListParams, PaginatedResult } from '@/shared/types/api'
import type { Company } from '../types/company'
import type { CompanyFormValues } from '../schemas/company-schema'

const BASE_URL = '/api/companies'

/** Danh mục pháp nhân. Lọc được cả mã số hiệu và cấp pháp nhân. */
export const companyApi = {
  list: (params: ListParams) => apiGet<PaginatedResult<Company>>(BASE_URL, { params }),

  getById: (id: number) => apiGet<Company>(`${BASE_URL}/${id}`),

  create: (payload: CompanyFormValues) => apiPost<Company>(BASE_URL, payload),

  update: (id: number, payload: Partial<CompanyFormValues>) =>
    apiPatch<Company>(`${BASE_URL}/${id}`, payload),

  remove: (id: number) => apiDelete<null>(`${BASE_URL}/${id}`),

  /** Logo đặt qua endpoint riêng, không nằm trong form. */
  uploadLogo: (id: number, file: File) => {
    const body = new FormData()
    body.append('file', file)
    return apiPost<{ logo: string }>(`${BASE_URL}/${id}/logo`, body)
  },
}
