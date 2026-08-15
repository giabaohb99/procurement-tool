import { apiDelete, apiGet, apiPatch, apiPost } from '@/core/api'
import type { ListParams, PaginatedResult } from '@/shared/types/api'
import type { DocumentPartner } from '../types/document-partner'
import type { DocumentType } from '../types/document-type'

/**
 * Hai danh mục nền của phân hệ Văn thư.
 *
 * Cả hai đều dưới 100 dòng nên màn hình nạp **một lần cả danh sách** rồi tìm và
 * lọc ngay tại trình duyệt — nhanh hơn và đỡ một vòng gọi mỗi lần gõ phím. Đừng
 * bắt chước cách này cho bảng văn bản: bảng đó phải phân trang từ backend.
 */
const CATALOG_PAGE_SIZE = 200

const DOC_TYPE_URL = '/api/doc-types'
const EXTERNAL_PARTY_URL = '/api/external-parties'

export type DocumentTypeInput = Omit<DocumentType, 'id'>
export type DocumentPartnerInput = Omit<DocumentPartner, 'id'>

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
