import { useInfiniteQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'

import { fetchUserPosts } from '../api/forum-api'

/**
 * Tủ bài viết của một người (trang cá nhân, QĐ-D3) — cùng khuôn con trỏ
 * `before_id` với feed chung; trang của CHÍNH MÌNH backend trả cả bài bị ẩn.
 */
export function useUserPosts(userId: number | undefined) {
  return useInfiniteQuery({
    queryKey: queryKeys.forum.userPosts(userId ?? 0),
    queryFn: ({ pageParam }) => fetchUserPosts(userId ?? 0, pageParam),
    initialPageParam: 0,
    getNextPageParam: (last) => (last.has_more ? last.next_before_id : undefined),
    enabled: userId !== undefined && Number.isInteger(userId) && userId > 0,
  })
}
