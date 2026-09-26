import { useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'

import { explainCustomsSearch } from '../api/customs-kind-api'

/**
 * bao-CR-495 — ô tìm tên hàng sẽ khớp những cách viết nào (từ đồng nghĩa + nồng độ tương đương),
 * để trang bày «đang tìm gì» ngay dưới ô tìm. Chỉ hỏi khi ô có chữ; đọc theo giá trị ĐÃ HOÃN.
 */
export function useCustomsSearchExplain(q: string) {
  const term = q.trim()
  return useQuery({
    queryKey: queryKeys.procurement.customsSearchExplain(term),
    queryFn: () => explainCustomsSearch(term),
    enabled: term.length > 0,
    staleTime: 60_000,
  })
}
