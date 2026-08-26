import { apiDelete, apiGet, apiPost } from '@/core/api'
import type {
  DocumentAmendment,
  DocumentIssuePreview,
  DocumentExcerptInput,
  DocumentLink,
  DocumentLinkInput,
  DocumentLinkList,
  DocumentLinkSlot,
  DocumentTreeNode,
  LinkedDocument,
} from '../types/document-link'
import type { IssueMailbox } from '../types/issue-mailbox'

const BASE_URL = '/api/documents'

export const documentLinkApi = {
  list: (documentId: number) =>
    apiGet<DocumentLinkList>(`${BASE_URL}/${documentId}/links`),

  /** E03 — các ô quan hệ theo loại, kèm sẵn danh sách văn bản chọn được. */
  slots: (documentId: number) =>
    apiGet<DocumentLinkSlot[]>(`${BASE_URL}/${documentId}/link-slots`),

  /** J04 — bản xem trước lúc ban hành. Chỉ đọc, không chiếm số. */
  issuePreview: (documentId: number) =>
    apiGet<DocumentIssuePreview>(`${BASE_URL}/${documentId}/issue-preview`),

  /** Hộp thư TÔI được gửi danh nghĩa khi ban hành văn bản này (26/08/2026). */
  issueMailboxes: (documentId: number) =>
    apiGet<IssueMailbox[]>(`${BASE_URL}/${documentId}/mailboxes`),

  /** J10 — văn bản này đã bị sửa đổi / thay thế / bãi bỏ bởi những văn bản nào. */
  amendedBy: (documentId: number) =>
    apiGet<DocumentAmendment[]>(`${BASE_URL}/${documentId}/amended-by`),

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
