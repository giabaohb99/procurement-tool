import { useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'

import { fetchPinnedForumPosts } from '../api/forum-api'

/** Bài đang ghim (F9a/CR-199) — dải đầu Bảng tin + tab «Thông báo». */
export function usePinnedPosts() {
  return useQuery({
    queryKey: queryKeys.forum.pinned(),
    queryFn: fetchPinnedForumPosts,
  })
}
