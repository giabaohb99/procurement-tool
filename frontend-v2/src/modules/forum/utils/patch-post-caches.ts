import type { InfiniteData, QueryClient } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'

import { fetchForumPost } from '../api/forum-api'
import type { ForumFeedPage, ForumPost } from '../types/forum-post'

/**
 * Vá MỘT bản PostOut mới vào mọi cache đang giữ bài đó (bài lẻ, feed, tủ cá
 * nhân, dải ghim) — cùng khuôn với cảm xúc (`use-toggle-post-reaction`). Chỉ
 * invalidate `post` thì thẻ trên feed và popup (đọc từ cache feed) vẫn hiện
 * dữ liệu cũ tới khi F5.
 */
export function patchPostInCaches(queryClient: QueryClient, fresh: ForumPost) {
  queryClient.setQueryData<ForumPost>(queryKeys.forum.post(fresh.id), fresh)
  const patchPages = (old: InfiniteData<ForumFeedPage> | undefined) =>
    old
      ? {
          ...old,
          pages: old.pages.map((page) => ({
            ...page,
            items: page.items.map((item) => (item.id === fresh.id ? fresh : item)),
          })),
        }
      : old
  queryClient.setQueriesData<InfiniteData<ForumFeedPage>>(
    { queryKey: queryKeys.forum.feed() },
    patchPages,
  )
  queryClient.setQueriesData<InfiniteData<ForumFeedPage>>(
    { queryKey: queryKeys.forum.userPostsAll() },
    patchPages,
  )
  queryClient.setQueryData<ForumPost[]>(queryKeys.forum.pinned(), (old) =>
    old?.map((item) => (item.id === fresh.id ? fresh : item)),
  )
}

/**
 * Nạp lại một bài từ máy chủ rồi vá vào mọi cache. Dùng khi thay đổi không trả
 * PostOut mới (tạo/xóa bình luận): không cộng/trừ tay vì xóa bình luận gốc
 * cuốn theo cả phản hồi nên delta không đoán được ở phía FE.
 */
export async function refreshPostInCaches(queryClient: QueryClient, postId: number) {
  try {
    const fresh = await fetchForumPost(postId)
    patchPostInCaches(queryClient, fresh)
  } catch {
    // Nạp bài lẻ hỏng (mất mạng…) — rơi về invalidate để lần render sau tự lo.
    void queryClient.invalidateQueries({ queryKey: queryKeys.forum.post(postId) })
  }
}
