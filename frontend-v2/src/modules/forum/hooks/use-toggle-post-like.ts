import { useMutation, useQueryClient, type InfiniteData } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'

import { toggleForumPostLike } from '../api/forum-api'
import type { ForumFeedPage, ForumPost } from '../types/forum-post'

/**
 * Bật/tắt thích một bài (F4, D-Q6: like KHÔNG có chuông).
 *
 * Không invalidate: một bài đang hiện ở ba chỗ (feed, tủ cá nhân, trang chi
 * tiết) — refetch cả ba là cuộn giật và tốn ba lượt gọi chỉ vì một cú bấm.
 * Backend đã trả trạng thái + số đếm chung cuộc, vá thẳng vào cache là đủ.
 */
export function useTogglePostLike() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: toggleForumPostLike,
    onSuccess: (result, postId) => {
      const patch = (post: ForumPost): ForumPost =>
        post.id === postId ? { ...post, liked: result.liked, like_count: result.count } : post

      queryClient.setQueryData<ForumPost>(queryKeys.forum.post(postId), (old) =>
        old ? patch(old) : old,
      )
      const patchPages = (old: InfiniteData<ForumFeedPage> | undefined) =>
        old
          ? {
              ...old,
              pages: old.pages.map((page) => ({ ...page, items: page.items.map(patch) })),
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
      // Dải ghim (F9a) cũng vẽ nút thích — thiếu nhánh này là bấm ở đó không nhúc nhích.
      queryClient.setQueryData<ForumPost[]>(queryKeys.forum.pinned(), (old) => old?.map(patch))
      // Hộp "ai đã thích" nếu đã từng mở thì con số vừa đổi — nạp lại lần mở sau.
      void queryClient.invalidateQueries({ queryKey: queryKeys.forum.postLikes(postId) })
    },
  })
}
