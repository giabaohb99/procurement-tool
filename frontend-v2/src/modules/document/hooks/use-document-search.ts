import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'
import { useDebouncedValue } from '@/shared/hooks/use-debounced-value'
import { documentSearchApi, type DocumentSearchParams } from '../api/document-search-api'

/** Hoãn 400ms trước khi gọi — riêng với debounce 350ms của ô tìm thường
 * (`useUrlSearchParam`): tìm toàn văn tốn hơn (MATCH AGAINST FULLTEXT + dựng
 * đoạn trích ở Python), nên chờ người dùng ngừng gõ lâu hơn một chút. */
const SEARCH_DEBOUNCE_MS = 400
/** Token dưới 2 ký tự không có ngram nào để khớp (chỉ mục `ngram` n=2 ở
 * backend) — gọi API cho câu 0–1 ký tự chỉ tốn một lượt round-trip vô ích.
 * Export ra để nơi dựng câu «rỗng» (`outgoing-documents-tab.tsx`,
 * `folder-documents-table.tsx`) dùng ĐÚNG một mốc, không chép số tay lần hai. */
export const MIN_QUERY_LENGTH = 2

/**
 * Câu tìm này có đi đường TÌM TOÀN VĂN không (25/09/2026, đại ca chốt bỏ công
 * tắc «Tìm cả nội dung» — tìm là tìm luôn cả tên lẫn nội dung). Đủ
 * `MIN_QUERY_LENGTH` ký tự → `/api/documents/search` (siêu dữ liệu + nội dung
 * soạn thảo + chữ trong tệp); ngắn hơn / rỗng → danh sách thường, vì chỉ mục
 * ngram không khớp được câu 1 ký tự và ô trống thì phải hiện đủ danh sách.
 */
export function isFullTextQuery(keyword: string): boolean {
  return keyword.trim().length >= MIN_QUERY_LENGTH
}

/**
 * TÌM KIẾM TOÀN VĂN văn bản (phase 07, duoc-CR-477) — đọc cả tiêu đề/số hiệu,
 * nội dung soạn thảo, và chữ trong tệp đính kèm.
 *
 * Debounce + trần độ dài nằm TRONG hook này, độc lập với debounce URL của
 * `useUrlSearchParam` ở nơi gọi — hook dùng được thẳng với state gõ tức thời
 * (`value` chưa qua debounce) mà vẫn không bắn API theo từng phím.
 *
 * `enabled=false` (mặc định công tắc «Tìm cả nội dung» tắt) → không gọi API
 * dù `q` hợp lệ, và React Query cũng không tự chạy lại khi bật lên nhờ
 * `enabled` đổi giá trị.
 */
export function useDocumentSearch(
  q: string,
  params: Omit<DocumentSearchParams, 'q'> = {},
  enabled = true,
) {
  const debouncedQ = useDebouncedValue(q, SEARCH_DEBOUNCE_MS)
  const trimmedQ = debouncedQ.trim()
  const canSearch = enabled && trimmedQ.length >= MIN_QUERY_LENGTH

  const queryParams: DocumentSearchParams = { ...params, q: trimmedQ }

  return useQuery({
    queryKey: queryKeys.document.search(queryParams),
    queryFn: () => documentSearchApi.search(queryParams),
    enabled: canSearch,
    //  Giữ kết quả cũ trong lúc nạp trang/từ khóa mới — bảng không nháy trắng.
    placeholderData: keepPreviousData,
  })
}
