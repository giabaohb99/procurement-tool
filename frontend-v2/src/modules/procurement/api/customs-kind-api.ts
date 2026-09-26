import { apiGet, apiPost } from '@/core/api'

import type { CustomsRetagResult } from '../types/customs-admin'

/**
 * Đường API riêng của hai danh mục cấu hình — bao-CR-494 / bao-CR-495. Hai danh mục tự nó
 * dùng khung CRUD chung (`/api/customs-kind-keywords`, `/api/customs-search-synonyms`), ở đây
 * chỉ còn hai việc lẻ. Tách khỏi `customs-api.ts` để không đụng tệp bao-CR-493 đang sửa.
 */

/** Gắn lại hoạt chất + nhãn Thành phẩm/Nguyên liệu cho MỌI dòng — chạy sau khi sửa từ khóa. */
export function retagCustomsKinds() {
  return apiPost<CustomsRetagResult>('/api/customs/kinds/retag')
}

export interface CustomsSearchExplain {
  include: { term: string; matches: string[] }[]
  exclude: { term: string; matches: string[] }[]
}

/** Ô tìm tên hàng sẽ khớp những cách viết nào (đồng nghĩa + nồng độ tương đương). */
export function explainCustomsSearch(q: string) {
  return apiGet<CustomsSearchExplain>('/api/customs/search/explain', { params: { q } })
}
