import { apiDelete, apiGet, apiPatch, apiPost, apiPut } from '@/core/api'
import type {
  DocFolderDetail,
  DocFolderSearchResult,
  DocFolderTreeNode,
  DocumentFolderRef,
  DocumentFolderSetInput,
  FolderAccessBulkGrantInput,
  FolderAccessBulkResult,
  FolderAccessEntry,
  FolderAccessGrantInput,
  FolderAccessLevelPatchInput,
  FolderCreateInput,
  FolderDeletePreview,
  FolderLinkDocumentsInput,
  FolderLinkResult,
  FolderReorderItem,
  FolderUnlinkDocumentsInput,
  FolderUpdateInput,
} from '../types/document-folder'

/**
 * API CÂY THƯ MỤC VĂN BẢN — `/api/doc-folders` + cửa hẹp
 * `PUT /api/documents/{id}/folders` (đặt thư mục của MỘT văn bản, nằm ở router
 * riêng phía backend nhưng gom vào đây vì cùng một domain phía frontend).
 *
 * Không phân trang: `/tree` trả danh sách PHẲNG (client tự dựng cây theo
 * `parent_id`), `/search` tự trần 50 dòng phía backend.
 */
const DOC_FOLDER_URL = '/api/doc-folders'

export const documentFolderApi = {
  tree: (includeArchived = false) =>
    apiGet<DocFolderTreeNode[]>(`${DOC_FOLDER_URL}/tree`, {
      params: { include_archived: includeArchived },
    }),

  search: (q: string) => apiGet<DocFolderSearchResult[]>(`${DOC_FOLDER_URL}/search`, { params: { q } }),

  getById: (id: number) => apiGet<DocFolderDetail>(`${DOC_FOLDER_URL}/${id}`),

  create: (payload: FolderCreateInput) => apiPost<DocFolderDetail>(DOC_FOLDER_URL, payload),

  update: (id: number, payload: FolderUpdateInput) =>
    apiPatch<DocFolderDetail>(`${DOC_FOLDER_URL}/${id}`, payload),

  move: (id: number, newParentId: number) =>
    apiPost<DocFolderDetail>(`${DOC_FOLDER_URL}/${id}/move`, { new_parent_id: newParentId }),

  /** Phải CÙNG CHA — backend gác quyền Quản lý trên đúng cha đó. */
  reorder: (items: FolderReorderItem[]) =>
    apiPost<{ changed: number }>(`${DOC_FOLDER_URL}/reorder`, { items }),

  /**
   * Xóa thư mục — chặn nếu còn thư mục con; còn văn bản thì KHÔNG chặn (25/09/2026):
   * văn bản chỉ nằm ở đây chuyển sang `moveTo`, bỏ trống = về thư mục pháp nhân.
   */
  remove: (id: number, moveTo?: number) =>
    apiDelete<null>(`${DOC_FOLDER_URL}/${id}`, moveTo ? { params: { move_to: moveTo } } : undefined),

  /** Đếm văn bản trong thư mục + số văn bản sẽ mồ côi nếu xóa (toàn hệ, không lọc quyền). */
  deletePreview: (id: number) => apiGet<FolderDeletePreview>(`${DOC_FOLDER_URL}/${id}/delete-preview`),

  /** Gắn HÀNG LOẠT văn bản vào một thư mục — `{moved, denied}`, không chặn cả lô vì một dòng lỗi. */
  linkDocuments: (payload: FolderLinkDocumentsInput) =>
    apiPost<FolderLinkResult>(`${DOC_FOLDER_URL}/documents/link`, payload),

  unlinkDocuments: (payload: FolderUnlinkDocumentsInput) =>
    apiPost<FolderLinkResult>(`${DOC_FOLDER_URL}/documents/unlink`, payload),

  /**
   * Đặt lại TOÀN BỘ thư mục của MỘT văn bản (màn tạo/sửa văn bản dùng cửa
   * này thay vì `linkDocuments`/`unlinkDocuments` — những hàm đó dành cho thao
   * tác HÀNG LOẠT từ màn Quản lý cây thư mục).
   */
  setDocumentFolders: (documentId: number, payload: DocumentFolderSetInput) =>
    apiPut<DocumentFolderRef[]>(`/api/documents/${documentId}/folders`, payload),

  /** Chỉ dòng ACL TRỰC TIẾP trên thư mục này (không kèm kế thừa) — cần mức Quản lý. */
  listAccess: (folderId: number) => apiGet<FolderAccessEntry[]>(`${DOC_FOLDER_URL}/${folderId}/access`),

  grantAccess: (folderId: number, payload: FolderAccessGrantInput) =>
    apiPost<FolderAccessEntry>(`${DOC_FOLDER_URL}/${folderId}/access`, payload),

  /**
   * Hộp «Chia sẻ» kiểu Drive — cấp CÙNG một mức cho CẢ danh sách chủ thể
   * trong một lượt, MỘT giao dịch phía backend (phase 10B). Không trả danh
   * sách dòng — nơi gọi tự `invalidateQueries` để nạp lại `listAccess`.
   */
  grantAccessBulk: (folderId: number, payload: FolderAccessBulkGrantInput) =>
    apiPost<FolderAccessBulkResult>(`${DOC_FOLDER_URL}/${folderId}/access/bulk`, payload),

  /** Đổi MỨC tại chỗ — menu thả xuống trên dòng «Người có quyền», không thu hồi rồi cấp lại. */
  updateAccessLevel: (folderId: number, accessId: number, payload: FolderAccessLevelPatchInput) =>
    apiPatch<FolderAccessEntry>(`${DOC_FOLDER_URL}/${folderId}/access/${accessId}`, payload),

  /**
   * Thu hồi = đánh dấu, dòng vẫn ở lại kèm mốc + lý do.
   *
   * ⚠️ DELETE có BODY — axios chỉ gửi được qua `config.data`, không phải tham
   * số body riêng như POST/PATCH (xem `apiDelete` ở `@/core/api`).
   */
  revokeAccess: (folderId: number, accessId: number, reason: string) =>
    apiDelete<FolderAccessEntry>(`${DOC_FOLDER_URL}/${folderId}/access/${accessId}`, {
      data: { reason },
    }),
}
