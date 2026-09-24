import { apiGet } from '@/core/api'
import type { PaginatedResult } from '@/shared/types/api'
import type { DocumentListParams } from './document-api'
import type { DocumentSearchResult } from '../types/document-search'

/**
 * API TÌM KIẾM TOÀN VĂN văn bản (phase 07, duoc-CR-477) —
 * `GET /api/documents/search`, router riêng khỏi `documentApi.list`
 * (`/api/documents`) dù cùng kết hợp được mọi bộ lọc của danh sách.
 *
 * Khác `documentApi.list`: `q` rỗng hoặc quá ngắn trả RỖNG tường minh (không
 * rơi về "liệt kê tất cả" như `q` của danh sách thường) — xem
 * `search_service.search` ở backend.
 */
const DOCUMENT_SEARCH_URL = '/api/documents/search'

export interface DocumentSearchParams extends Omit<DocumentListParams, 'q'> {
  q: string
}

export const documentSearchApi = {
  search: (params: DocumentSearchParams) =>
    apiGet<PaginatedResult<DocumentSearchResult>>(DOCUMENT_SEARCH_URL, { params }),
}
