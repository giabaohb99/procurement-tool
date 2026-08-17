import { apiDelete, apiGet, apiPost } from '@/core/api'
import type { PaginatedResult } from '@/shared/types/api'
import type { PurchaseOrder } from '../types/purchase-document'

export interface AttachmentFile {
  id: number
  file_id: number
  filename: string
  /**
   * Đường đọc thẳng kho lưu trữ, KHÔNG qua kiểm quyền.
   *
   * Backend để rỗng với entity riêng tư (`document_version`) — chỗ nào nhận
   * chuỗi rỗng thì phải tải qua `GET /api/attachments/{id}/download` bằng
   * `downloadFile` của `@/core/api`.
   */
  url: string
  content_type: string
  size: number
  /** Mã băm SHA-256 nội dung, tính lúc tải lên. Tệp tải lên trước 17/08/2026 để rỗng. */
  sha256: string
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

/** Một người trong danh sách gợi ý khi gõ `@`. */
export interface MentionablePerson {
  user_id: number
  name: string
  code: string
  avatar: string
  /** Có liên quan sẵn tới phiếu (người tạo / đã bình luận) — xếp lên đầu. */
  related: boolean
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

export interface UnitOption {
  id: number
  code: string
  name: string
}

export interface ItemGroupOption {
  id: number
  code: string
  name: string
  std_days: string
  std_days_unavail: string
}

export interface ProductOption {
  id: number
  code: string
  name: string
  item_group: string
  unit: string
  thumbnail_url?: string
}

export interface PurchaseHistoryExtra {
  item_group?: string
  warehouse_code?: string
  item_note?: string
  invoice_name?: string
  spec?: string
  fg_code?: string
  fg_name?: string
  [key: string]: unknown
}

export interface PurchaseHistoryRow {
  id: number
  po_id: number
  po_code: string
  source: string
  product_code: string
  product_name: string
  supplier_code: string
  supplier_name: string
  company_id: number
  company_name: string
  order_date: string
  unit: string
  qty_order: number
  price: number
  vat: number
  amount: number
  completed_at: string
  extra: PurchaseHistoryExtra
}

const ATTACHMENT_URL = '/api/attachments'
const COMMENT_URL = '/api/comments'

export const purchaseRequestSupportApi = {
  listWarehouses: () =>
    apiGet<PaginatedResult<WarehouseOption>>('/api/warehouses', {
      params: { page: 1, page_size: 200 },
    }),

  listUnits: () =>
    apiGet<PaginatedResult<UnitOption>>('/api/units', {
      params: { page: 1, page_size: 200, is_active: true },
    }),

  listItemGroups: () =>
    apiGet<PaginatedResult<ItemGroupOption>>('/api/item-groups', {
      params: { page: 1, page_size: 500, is_active: true },
    }),

  listProducts: (search = '') =>
    apiGet<PaginatedResult<ProductOption>>('/api/products', {
      params: { page: 1, page_size: 30, search, is_active: true },
    }),

  listProductPurchaseHistory: (
    productCode: string,
    page: number,
    pageSize: number,
    search = '',
  ) =>
    apiGet<PaginatedResult<PurchaseHistoryRow>>(
      `/api/products/${encodeURIComponent(productCode)}/purchase-history`,
      { params: { page, page_size: pageSize, search } },
    ),

  listAttachments: (entity: string, entityId: number) =>
    apiGet<AttachmentFile[]>(ATTACHMENT_URL, {
      params: { entity, entity_id: entityId },
    }),

  listDocumentTypes: () => apiGet<DocumentTypeOption[]>(`${ATTACHMENT_URL}/doc-types`),

  /**
   * `purchaseOrderId` chỉ dùng cho tệp gắn vào LẦN GIAO (`entity = 'delivery'`):
   * backend cần biết đơn cha để kiểm tra phạm vi dữ liệu, dòng giao không tự
   * suy ngược ra đơn được.
   */
  uploadAttachments: (
    entity: string,
    entityId: number,
    files: File[],
    docType = '',
    purchaseOrderId = 0,
  ) => {
    const body = new FormData()
    body.append('entity', entity)
    body.append('entity_id', String(entityId))
    body.append('doc_type', docType)
    if (purchaseOrderId > 0) body.append('purchase_order_id', String(purchaseOrderId))
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

  /** `entity`: `purchase_request` | `purchase_order` — cùng một API bình luận. */
  listComments: (entity: string, entityId: number, beforeId = 0) =>
    apiGet<CommentPage>(COMMENT_URL, {
      params: {
        entity,
        entity_id: entityId,
        limit: 10,
        before_id: beforeId || undefined,
      },
    }),

  /**
   * Gợi ý người để `@` khi đang gõ bình luận.
   *
   * Chưa gõ chữ nào (`q` rỗng) thì backend chỉ trả người ĐANG DÍNH TỚI PHIẾU
   * (người tạo + người đã bình luận); gõ rồi thì tìm trong toàn bộ nhân sự.
   */
  listMentionable: (entity: string, entityId: number, q = '') =>
    apiGet<MentionablePerson[]>(`${COMMENT_URL}/mentionable`, {
      params: { entity, entity_id: entityId, q },
    }),

  listReplies: (commentId: number) =>
    apiGet<PurchaseRequestComment[]>(`${COMMENT_URL}/${commentId}/replies`),

  createComment: (
    entity: string,
    entityId: number,
    body: string,
    parentId = 0,
    fileIds: number[] = [],
  ) =>
    apiPost<PurchaseRequestComment>(COMMENT_URL, {
      entity,
      entity_id: entityId,
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
