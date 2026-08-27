import { useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'

import { fetchForumPostLikes } from '../api/forum-api'

/** Ai đã thích một bài — chỉ gọi khi hộp thoại đang mở (`enabled`). */
export function usePostLikes(postId: number, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.forum.postLikes(postId),
    queryFn: () => fetchForumPostLikes(postId),
    enabled: enabled && postId > 0,
  })
}
