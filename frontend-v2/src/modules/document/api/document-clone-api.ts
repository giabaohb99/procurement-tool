import { apiGet, apiPatch, apiPost } from '@/core/api'
import type { LinkedDocument } from '../types/document-link'
import type { DocumentCloneInput, DocumentCloneList } from '../types/document-clone'

const BASE_URL = '/api/documents'

export const documentCloneApi = {
  /** F10 — bảng theo dõi, kèm danh sách pháp nhân chưa nhận. */
  list: (documentId: number) =>
    apiGet<DocumentCloneList>(`${BASE_URL}/${documentId}/clones`),

  create: (documentId: number, values: DocumentCloneInput) =>
    apiPost<LinkedDocument[]>(`${BASE_URL}/${documentId}/clones`, values),

  updateStatus: (documentId: number, cloneStatus: number) =>
    apiPatch<LinkedDocument>(`${BASE_URL}/${documentId}/clone-status`, {
      clone_status: cloneStatus,
    }),
}
