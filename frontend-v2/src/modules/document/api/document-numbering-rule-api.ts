import { apiDelete, apiGet, apiPatch, apiPost } from '@/core/api'
import type { PaginatedResult } from '@/shared/types/api'
import type {
  DocumentNumberingRule,
  DocumentNumberingRuleInput,
  NumberingDirection,
} from '../types/document-numbering-rule'

const BASE_URL = '/api/document-numbering-rules'

export const documentNumberingRuleApi = {
  list: (direction?: NumberingDirection) =>
    apiGet<PaginatedResult<DocumentNumberingRule>>(BASE_URL, {
      params: direction ? { direction } : {},
    }),
  create: (payload: DocumentNumberingRuleInput) =>
    apiPost<DocumentNumberingRule>(BASE_URL, payload),
  update: (id: number, payload: Partial<DocumentNumberingRuleInput>) =>
    apiPatch<DocumentNumberingRule>(`${BASE_URL}/${id}`, payload),
  remove: (id: number) => apiDelete<null>(`${BASE_URL}/${id}`),
}
