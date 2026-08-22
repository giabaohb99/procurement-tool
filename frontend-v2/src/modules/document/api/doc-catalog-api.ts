import { apiDelete, apiGet, apiPatch, apiPost } from '@/core/api'
import type { ListParams, PaginatedResult } from '@/shared/types/api'
import type { DocumentPartner } from '../types/document-partner'
import type { DocumentType } from '../types/document-type'
import type { SecurityLevel, SecurityLevelEditableFields } from '../types/security-level'

/**
 * Ba danh mục nền của phân hệ Văn thư.
 *
 * Cả ba đều dưới 100 dòng nên màn hình nạp **một lần cả danh sách** rồi tìm và
 * lọc ngay tại trình duyệt — nhanh hơn và đỡ một vòng gọi mỗi lần gõ phím. Đừng
 * bắt chước cách này cho bảng văn bản: bảng đó phải phân trang từ backend.
 */
const CATALOG_PAGE_SIZE = 200

const DOC_TYPE_URL = '/api/doc-types'
const EXTERNAL_PARTY_URL = '/api/external-parties'
const SECURITY_LEVEL_URL = '/api/security-levels'

export type DocumentTypeInput = Omit<DocumentType, 'id'>
export type DocumentPartnerInput = Omit<DocumentPartner, 'id'>
export type SecurityLevelCreateInput = Omit<SecurityLevel, 'id'>
export type SecurityLevelUpdateInput = SecurityLevelEditableFields

export const docTypeApi = {
  list: (params: ListParams = {}) =>
    apiGet<PaginatedResult<DocumentType>>(DOC_TYPE_URL, {
      params: { page: 1, page_size: CATALOG_PAGE_SIZE, ...params },
    }),

  getById: (id: number) => apiGet<DocumentType>(`${DOC_TYPE_URL}/${id}`),

  create: (payload: DocumentTypeInput) => apiPost<DocumentType>(DOC_TYPE_URL, payload),

  update: (id: number, payload: Partial<DocumentTypeInput>) =>
    apiPatch<DocumentType>(`${DOC_TYPE_URL}/${id}`, payload),

  remove: (id: number) => apiDelete<null>(`${DOC_TYPE_URL}/${id}`),
}

export const externalPartyApi = {
  list: (params: ListParams = {}) =>
    apiGet<PaginatedResult<DocumentPartner>>(EXTERNAL_PARTY_URL, {
      params: { page: 1, page_size: CATALOG_PAGE_SIZE, ...params },
    }),

  getById: (id: number) => apiGet<DocumentPartner>(`${EXTERNAL_PARTY_URL}/${id}`),

  create: (payload: DocumentPartnerInput) =>
    apiPost<DocumentPartner>(EXTERNAL_PARTY_URL, payload),

  update: (id: number, payload: Partial<DocumentPartnerInput>) =>
    apiPatch<DocumentPartner>(`${EXTERNAL_PARTY_URL}/${id}`, payload),

  remove: (id: number) => apiDelete<null>(`${EXTERNAL_PARTY_URL}/${id}`),
}

export const securityLevelApi = {
  list: (params: ListParams = {}) =>
    apiGet<PaginatedResult<SecurityLevel>>(SECURITY_LEVEL_URL, {
      params: { page: 1, page_size: CATALOG_PAGE_SIZE, ...params },
    }),

  getById: (id: number) => apiGet<SecurityLevel>(`${SECURITY_LEVEL_URL}/${id}`),

  create: (payload: SecurityLevelCreateInput) =>
    apiPost<SecurityLevel>(SECURITY_LEVEL_URL, payload),

  //  `kind` và `value` KHÔNG nằm trong `SecurityLevelUpdateInput` — backend cố ý
  //  không nhận hai trường này ở PATCH (xem `security_level_schema.py`).
  update: (id: number, payload: Partial<SecurityLevelUpdateInput>) =>
    apiPatch<SecurityLevel>(`${SECURITY_LEVEL_URL}/${id}`, payload),

  remove: (id: number) => apiDelete<null>(`${SECURITY_LEVEL_URL}/${id}`),
}
