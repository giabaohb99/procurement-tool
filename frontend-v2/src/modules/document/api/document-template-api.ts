import { apiDelete, apiGet, apiPatch, apiPost } from '@/core/api'
import type { ListParams, PaginatedResult } from '@/shared/types/api'
import type {
  DocumentTemplate,
  DocumentTemplateInput,
  DocumentTemplateListItem,
} from '../types/document-template'

const DOCUMENT_TEMPLATE_URL = '/api/document-templates'

export const documentTemplateApi = {
  list: (params: ListParams = {}) =>
    apiGet<PaginatedResult<DocumentTemplateListItem>>(DOCUMENT_TEMPLATE_URL, {
      params: { page: 1, page_size: 200, ...params },
    }),

  getById: (id: number) => apiGet<DocumentTemplate>(`${DOCUMENT_TEMPLATE_URL}/${id}`),

  create: (payload: DocumentTemplateInput) =>
    apiPost<DocumentTemplate>(DOCUMENT_TEMPLATE_URL, payload),

  update: (id: number, payload: Partial<DocumentTemplateInput>) =>
    apiPatch<DocumentTemplate>(`${DOCUMENT_TEMPLATE_URL}/${id}`, payload),

  remove: (id: number) => apiDelete<null>(`${DOCUMENT_TEMPLATE_URL}/${id}`),
}
