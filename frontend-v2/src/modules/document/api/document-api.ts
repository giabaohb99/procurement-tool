import type { AxiosRequestConfig } from 'axios'

import { apiDelete, apiGet, apiPatch, apiPost } from '@/core/api'
import type { ListParams, PaginatedResult } from '@/shared/types/api'
import type { DocumentAccess, DocumentAccessInput } from '../types/document-access'
import type { DocPrerequisite } from '../types/document-link-rule'
import type {
  DocumentPermissions,
  DocumentRecord,
  DocumentSuggestion,
  DocumentVersion,
  NumberPreview,
} from '../types/document-record'

/**
 * API VĂN BẢN.
 *
 * Khác ba danh mục nền (nạp cả danh sách một lần rồi lọc tại trình duyệt):
 * bảng văn bản **phân trang từ backend** và tìm kiếm cũng ở backend — bảng này
 * sẽ lên vài chục nghìn dòng, mà quan trọng hơn: lọc ở client thì trình duyệt
 * phải nhận về cả những văn bản người dùng KHÔNG được xem.
 */
const DOCUMENT_URL = '/api/documents'

export interface DocumentListParams extends ListParams {
  /** Hỏi đích danh các BẢN RIÊNG của một bản gốc (dùng khi bung dòng). */
  source_document_id?: number
  /** Tìm theo tiêu đề, số hiệu, số hiệu CŨ, từ khóa. */
  q?: string
  doc_type_id?: number
  company_id?: number
  department_id?: number
  /** Liệt kê văn bản của MỘT quyển sổ — màn sổ văn bản dùng. */
  book_id?: number
  status?: number
  secrecy_level?: number
  effective_from?: string
  effective_to?: string
}

/** Bộ trường chung C01 — đúng những gì người soạn khai được. */
export interface DocumentInput {
  doc_type_id: number
  company_id: number
  department_id: number | null
  book_id: number | null
  owner_employee_id: number
  drafter_employee_id: number | null
  signer_employee_id: number | null
  title: string
  summary: string
  keywords: string
  secrecy_level: number | null
  urgency: number
  effective_date: string | null
  expire_date: string | null
  legacy_code: string
}

export interface VersionInput {
  /** 1 sửa lớn (lên 2.0) · 2 sửa nhỏ (lên 1.1). */
  change_kind: number
  change_summary: string
  change_reason: string
  effective_from: string | null
}

export const documentApi = {
  list: (params: DocumentListParams = {}) =>
    apiGet<PaginatedResult<DocumentRecord>>(DOCUMENT_URL, {
      params: { page: 1, page_size: 20, ...params },
    }),

  getById: (id: number) => apiGet<DocumentRecord>(`${DOCUMENT_URL}/${id}`),

  create: (payload: DocumentInput & { content_html?: string }) =>
    apiPost<DocumentRecord>(DOCUMENT_URL, payload),

  update: (id: number, payload: Partial<DocumentInput>) =>
    apiPatch<DocumentRecord>(`${DOCUMENT_URL}/${id}`, payload),

  /** Xác nhận đã rà soát xong — tắt cờ «cần rà lại», kết luận vào nhật ký. */
  confirmReviewed: (id: number, ket_luan: string) =>
    apiPost<DocumentRecord>(`${DOCUMENT_URL}/${id}/reviewed`, { ket_luan }),

  updateIssueNumber: (id: number, payload: { issue_number: string; reason: string }) =>
    apiPatch<DocumentRecord>(`${DOCUMENT_URL}/${id}/issue-number`, payload),

  remove: (id: number) => apiDelete<null>(`${DOCUMENT_URL}/${id}`),

  submit: (id: number) => apiPost<DocumentRecord>(`${DOCUMENT_URL}/${id}/submit`, {}),
  /** `applyMode` = cơ chế áp dụng chọn lúc ban hành (F13). Bỏ trống là giữ nguyên. */
  approve: (id: number, applyMode?: number) =>
    apiPost<DocumentRecord>(`${DOCUMENT_URL}/${id}/approve`, { apply_mode: applyMode ?? null }),
  reject: (id: number, reason: string) =>
    apiPost<DocumentRecord>(`${DOCUMENT_URL}/${id}/reject`, { reason }),
  //  Bãi bỏ = lối gỡ bỏ của văn bản ĐÃ cấp số; xóa hẳn thì backend từ chối vì
  //  số đã nằm trong sổ.
  revoke: (id: number, reason: string) =>
    apiPost<DocumentRecord>(`${DOCUMENT_URL}/${id}/revoke`, { reason }),

  /** Văn bản cùng loại cùng phòng đang hiệu lực — hiện ngay trong form soạn (B05). */
  suggestions: (params: {
    doc_type_id: number
    department_id?: number | null
    company_id?: number | null
    exclude_id?: number
  }) => apiGet<DocumentSuggestion[]>(`${DOCUMENT_URL}/suggestions`, { params }),

  /**
   * Quan hệ tiên quyết còn thiếu của một LOẠI — hỏi trước khi tạo (E04b).
   *
   * Rỗng nghĩa là tạo thẳng. Có dòng nào thì màn tạo hỏi lại một nhịp, người
   * dùng chọn tiếp tục thì văn bản vẫn được tạo.
   */
  prerequisites: (docTypeId: number) =>
    apiGet<DocPrerequisite[]>(`${DOCUMENT_URL}/prerequisite-check`, {
      params: { doc_type_id: docTypeId },
    }),

  /**
   * Số hiệu SẼ cấp. Chỉ để xem trước — **không chiếm số**, và có thể lệch nếu
   * có người được cấp số ngay sau khi màn hình đọc xong.
   */
  numberPreview: (params: {
    doc_type_id: number
    company_id: number
    department_id?: number | null
    book_id?: number | null
  }) => apiGet<NumberPreview>(`${DOCUMENT_URL}/number-preview`, { params }),
}

export const documentVersionApi = {
  list: (documentId: number) => apiGet<DocumentVersion[]>(`${DOCUMENT_URL}/${documentId}/versions`),

  /** Kèm `content_html` — chỉ trang soạn thảo gọi, danh sách phiên bản thì không. */
  getById: (documentId: number, versionId: number) =>
    apiGet<DocumentVersion>(`${DOCUMENT_URL}/${documentId}/versions/${versionId}`),

  create: (documentId: number, payload: VersionInput) =>
    apiPost<DocumentVersion>(`${DOCUMENT_URL}/${documentId}/versions`, payload),

  saveContent: (
    documentId: number,
    versionId: number,
    payload: {
      content_html?: string
      change_summary?: string
      effective_from?: string | null
      //  Lề trang (mm) — kéo thước thì chỉ gửi hai số này, không gửi thân bài.
      margin_left_mm?: number
      margin_right_mm?: number
      auto_heading_number?: boolean
      header_left?: string
      header_right?: string
      footer_left?: string
      footer_right?: string
    },
  ) =>
    apiPatch<DocumentVersion>(
      `${DOCUMENT_URL}/${documentId}/versions/${versionId}`,
      payload,
      // Cờ riêng của http-client: tự động lưu chạy theo nhịp gõ, hỏng một nhịp
      // thì báo bằng trạng thái "chưa lưu" trên đầu trang chứ không bắn toast
      // đè lên chỗ đang gõ.
      { _silent: true } as AxiosRequestConfig,
    ),
}

export const documentAccessApi = {
  list: (documentId: number) => apiGet<DocumentAccess[]>(`${DOCUMENT_URL}/${documentId}/access`),

  grant: (documentId: number, payload: DocumentAccessInput) =>
    apiPost<DocumentAccess>(`${DOCUMENT_URL}/${documentId}/access`, payload),

  /** Thu hồi = đánh dấu; dòng vẫn ở lại bảng kèm mốc và lý do. */
  revoke: (documentId: number, accessId: number, reason: string) =>
    apiPost<DocumentAccess>(`${DOCUMENT_URL}/${documentId}/access/${accessId}/revoke`, { reason }),

  /** Tôi được làm gì trên văn bản này — chỉ để ẩn nút, không phải bảo mật. */
  permissions: (documentId: number) =>
    apiGet<DocumentPermissions>(`${DOCUMENT_URL}/${documentId}/permissions`),
}
