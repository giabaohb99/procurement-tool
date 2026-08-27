import { useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'

import { fetchForumPost } from '../api/forum-api'

/** Một bài viết cho trang `/forum/posts/:id`. Ngoài đối tượng xem thì lỗi 403. */
export function useForumPost(id: number) {
  return useQuery({
    queryKey: queryKeys.forum.post(id),
    queryFn: () => fetchForumPost(id),
    enabled: Number.isInteger(id) && id > 0,
    // 403/404 là câu trả lời chung cuộc, thử lại chỉ tốn lượt gọi.
    retry: false,
  })
}
