import { useInfiniteQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'

import { fetchForumFeed } from '../api/forum-api'

/**
 * Feed cuộn vô hạn theo con trỏ `before_id`: trang sau bắt đầu từ id nhỏ nhất
 * của trang trước, nên bài mới chen vào giữa không làm lặp/sót dòng (mục 4.3
 * của doc `erp/dien-dan/01`).
 */
export function useForumFeed() {
  return useInfiniteQuery({
    queryKey: queryKeys.forum.feed(),
    queryFn: ({ pageParam }) => fetchForumFeed(pageParam),
    initialPageParam: 0,
    getNextPageParam: (last) => (last.has_more ? last.next_before_id : undefined),
  })
}
