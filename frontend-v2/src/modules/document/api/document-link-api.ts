import { apiDelete, apiGet, apiPost } from '@/core/api'
import type {
  DocumentExcerptInput,
  DocumentLink,
  DocumentLinkInput,
  DocumentLinkList,
  DocumentLinkSlot,
  DocumentTreeNode,
  LinkedDocument,
} from '../types/document-link'

const BASE_URL = '/api/documents'

export const documentLinkApi = {
  list: (documentId: number) =>
    apiGet<DocumentLinkList>(`${BASE_URL}/${documentId}/links`),

  /** E03 — các ô quan hệ theo loại, kèm sẵn danh sách văn bản chọn được. */
  slots: (documentId: number) =>
    apiGet<DocumentLinkSlot[]>(`${BASE_URL}/${documentId}/link-slots`),

  tree: (documentId: number) =>
    apiGet<DocumentTreeNode>(`${BASE_URL}/${documentId}/tree`),

  create: (documentId: number, values: DocumentLinkInput) =>
    apiPost<DocumentLink>(`${BASE_URL}/${documentId}/links`, values),

  remove: (documentId: number, linkId: number) =>
    apiDelete<null>(`${BASE_URL}/${documentId}/links/${linkId}`),

  listExcerpts: (documentId: number) =>
    apiGet<DocumentLink[]>(`${BASE_URL}/${documentId}/excerpts`),

  createExcerpt: (documentId: number, values: DocumentExcerptInput) =>
    apiPost<LinkedDocument>(`${BASE_URL}/${documentId}/excerpts`, values),
}
