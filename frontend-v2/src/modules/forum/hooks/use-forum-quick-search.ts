import { useEffect, useState } from 'react'
import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'

import { searchForumPosts } from '../api/forum-api'

/** Số bài sổ xuống dưới ô tìm — muốn xem hết thì bấm «Xem tất cả» qua trang Tìm bài. */
export const QUICK_SEARCH_LIMIT = 5
/** Dưới 2 ký tự chưa tìm — 1 chữ cái LIKE quét gần hết diễn đàn, gợi ý vô nghĩa. */
export const QUICK_SEARCH_MIN_CHARS = 2

/**
 * Top 5 bài khớp từ khóa cho dropdown gợi ý trên header (bao-CR-273.1). Debounce
 * nằm TRONG hook (250ms): gõ từng phím không được bắn API, nhưng component chỉ
 * việc đưa nguyên chữ đang gõ vào. `enabled` do component quyết — chỉ tìm khi
 * dropdown đang mở, đóng rồi thì thôi.
 */
export function useForumQuickSearch(keyword: string, enabled: boolean) {
  const q = keyword.trim()
  const [debouncedQ, setDebouncedQ] = useState(q)
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQ(q), 250)
    return () => clearTimeout(timer)
  }, [q])

  //  Cả chữ ĐANG GÕ lẫn chữ đã debounce đều phải đủ dài — thiếu vế đầu thì xóa
  //  bớt còn 1 ký tự vẫn bắn query cũ; thiếu vế sau thì chữ ngắn lọt xuống API.
  const ready =
    enabled &&
    q.length >= QUICK_SEARCH_MIN_CHARS &&
    debouncedQ.length >= QUICK_SEARCH_MIN_CHARS

  return useQuery({
    // why: thêm khóa `quick` để không đụng cache trang Tìm bài (cùng tiền tố
    // ['forum','search'] cho kiểm duyệt invalidate cả cụm một lần).
    queryKey: queryKeys.forum.search({ q: debouncedQ, quick: QUICK_SEARCH_LIMIT }),
    queryFn: () =>
      searchForumPosts({ q: debouncedQ, page: 1, per_page: QUICK_SEARCH_LIMIT }),
    enabled: ready,
    placeholderData: keepPreviousData,
    staleTime: 30_000,
  })
}
