import { apiDelete, apiGet, apiPost } from '@/core/api'
import type { PaginatedResult } from '@/shared/types/api'
import type { PurchaseOrder } from '../types/purchase-document'

export interface AttachmentFile {
  id: number
  file_id: number
  filename: string
  url: string
  content_type: string
  size: number
  doc_type: string
  entity: string
  entity_id: number
}

export interface DocumentTypeOption {
  value: string
  label: string
}

export interface CommentFile {
  link_id: number
  filename: string
  url: string
  content_type: string
  size: number
  is_image: boolean
}

export interface CommentMention {
  user_id: number
  name: string
}

export interface PurchaseRequestComment {
  id: number
  entity: string
  entity_id: number
  body: string
  parent_id: number
  author_id: number
  author_name: string
  author_code: string
  author_avatar: string
  created_at: string
  can_delete: boolean
  like_count: number
  liked: boolean
  reply_count?: number
  reply_to_user_id: number
  reply_to_name: string
  mentions: CommentMention[]
  files: CommentFile[]
}

export interface CommentPage {
  items: PurchaseRequestComment[]
  total: number
  total_roots: number
  older_count: number
  oldest_id: number
}

export interface UploadedFile {
  file_id: number
  filename: string
  url: string
  content_type: string
  size: number
}

export interface WarehouseOption {
  id: number
  code: string
  name: string
}

const ATTACHMENT_URL = '/api/attachments'
const COMMENT_URL = '/api/comments'

export const purchaseRequestSupportApi = {
  listWarehouses: () =>
    apiGet<PaginatedResult<WarehouseOption>>('/api/warehouses', {
      params: { page: 1, page_size: 200 },
    }),

  listAttachments: (entity: string, entityId: number) =>
    apiGet<AttachmentFile[]>(ATTACHMENT_URL, {
      params: { entity, entity_id: entityId },
    }),

  listDocumentTypes: () => apiGet<DocumentTypeOption[]>(`${ATTACHMENT_URL}/doc-types`),

  uploadAttachments: (entity: string, entityId: number, files: File[], docType = '') => {
    const body = new FormData()
    body.append('entity', entity)
    body.append('entity_id', String(entityId))
    body.append('doc_type', docType)
    files.forEach((file) => body.append('files', file))
    return apiPost<AttachmentFile[]>(ATTACHMENT_URL, body)
  },

  deleteAttachment: (linkId: number) => apiDelete<null>(`${ATTACHMENT_URL}/${linkId}`),

  uploadCommentFiles: (files: File[]) => {
    const body = new FormData()
    body.append('entity', 'comment')
    files.forEach((file) => body.append('files', file))
    return apiPost<UploadedFile[]>(`${ATTACHMENT_URL}/upload-file`, body)
  },

  listComments: (purchaseRequestId: number, beforeId = 0) =>
    apiGet<CommentPage>(COMMENT_URL, {
      params: {
        entity: 'purchase_request',
        entity_id: purchaseRequestId,
        limit: 10,
        before_id: beforeId || undefined,
      },
    }),

  listReplies: (commentId: number) =>
    apiGet<PurchaseRequestComment[]>(`${COMMENT_URL}/${commentId}/replies`),

  createComment: (
    purchaseRequestId: number,
    body: string,
    parentId = 0,
    fileIds: number[] = [],
  ) =>
    apiPost<PurchaseRequestComment>(COMMENT_URL, {
      entity: 'purchase_request',
      entity_id: purchaseRequestId,
      body,
      parent_id: parentId,
      file_ids: fileIds,
    }),

  toggleLike: (commentId: number) =>
    apiPost<{ liked: boolean; count: number }>(`${COMMENT_URL}/${commentId}/like`, {}),

  deleteComment: (commentId: number) => apiDelete<null>(`${COMMENT_URL}/${commentId}`),

  listRelatedPurchaseOrders: (purchaseRequestCode: string) =>
    apiGet<PaginatedResult<PurchaseOrder>>('/api/purchase-orders', {
      params: { pr_code: purchaseRequestCode, page: 1, page_size: 200 },
    }),
}
