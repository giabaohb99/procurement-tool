import { apiDelete, apiGet, apiPost } from '@/core/api'
import type { DocumentRecord } from '../types/document-record'
import type {
  DocumentScope,
  DocumentScopeInput,
  DocumentScopeList,
  ScopeOptions,
} from '../types/document-scope'

const BASE_URL = '/api/documents'

export const documentScopeApi = {
  list: (documentId: number) =>
    apiGet<DocumentScopeList>(`${BASE_URL}/${documentId}/scopes`),

  options: () => apiGet<ScopeOptions>(`${BASE_URL}/scope-options`),

  create: (documentId: number, values: DocumentScopeInput) =>
    apiPost<DocumentScope>(`${BASE_URL}/${documentId}/scopes`, values),

  remove: (documentId: number, scopeId: number) =>
    apiDelete<null>(`${BASE_URL}/${documentId}/scopes/${scopeId}`),

  /** F05 — văn bản đang áp dụng cho chính người đang đăng nhập. */
  appliesToMe: () =>
    apiGet<{ total: number; items: DocumentRecord[] }>(`${BASE_URL}/applies-to-me`),
}
