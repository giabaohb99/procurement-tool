import { apiDelete, apiGet, apiPatch, apiPost } from '@/core/api'
import type { ListParams, PaginatedResult } from '@/shared/types/api'
import type { BookCounter, DocumentBook, DocumentBookInput } from '../types/document-book'

/**
 * SỔ VĂN BẢN.
 *
 * ⚠️ **Không có endpoint "cấp một số".** Số phải cấp trong cùng transaction với
 * việc ghi bản ghi mang số đó — mở đường cấp số đứng riêng là mời gọi cảnh gọi
 * xong, ghi bản ghi lỗi, số biến mất khỏi sổ mà không ai biết. Màn hình chỉ đọc
 * `next_no` để xem trước.
 */
const BASE_URL = '/api/document-books'

/** Danh mục sổ nhỏ (vài chục dòng) nên nạp một lần rồi lọc tại trình duyệt. */
const PAGE_SIZE = 200

export const documentBookApi = {
  list: (params: ListParams = {}) =>
    apiGet<PaginatedResult<DocumentBook>>(BASE_URL, {
      params: { page: 1, page_size: PAGE_SIZE, ...params },
    }),

  getById: (id: number) => apiGet<DocumentBook>(`${BASE_URL}/${id}`),

  create: (payload: DocumentBookInput) => apiPost<DocumentBook>(BASE_URL, payload),

  update: (id: number, payload: Partial<DocumentBookInput>) =>
    apiPatch<DocumentBook>(`${BASE_URL}/${id}`, payload),

  remove: (id: number) => apiDelete<null>(`${BASE_URL}/${id}`),

  /** Tình trạng bộ đếm của một năm — cho khối "Bộ đếm" trên trang chi tiết. */
  counter: (id: number, year?: number) =>
    apiGet<BookCounter>(`${BASE_URL}/${id}/counter`, { params: year ? { year } : {} }),
}
