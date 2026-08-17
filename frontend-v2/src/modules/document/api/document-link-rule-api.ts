import { apiDelete, apiGet, apiPatch, apiPost } from '@/core/api'
import type {
  DocTypeLinkRule,
  DocTypeLinkRuleInput,
  LinkRuleOptions,
} from '../types/document-link-rule'

const BASE_URL = '/api/doc-type-link-rules'

export const documentLinkRuleApi = {
  list: () => apiGet<{ total: number; items: DocTypeLinkRule[] }>(BASE_URL),
  getById: (id: number) => apiGet<DocTypeLinkRule>(`${BASE_URL}/${id}`),
  options: () => apiGet<LinkRuleOptions>(`${BASE_URL}/options`),
  create: (values: DocTypeLinkRuleInput) => apiPost<DocTypeLinkRule>(BASE_URL, values),
  update: (id: number, values: DocTypeLinkRuleInput) =>
    apiPatch<DocTypeLinkRule>(`${BASE_URL}/${id}`, values),
  remove: (id: number) => apiDelete<null>(`${BASE_URL}/${id}`),
}
