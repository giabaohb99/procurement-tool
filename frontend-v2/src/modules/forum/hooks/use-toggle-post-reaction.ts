import { useMutation, useQueryClient, type InfiniteData } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'

import { toggleForumPostReaction } from '../api/forum-api'
import type { ForumFeedPage, ForumPost } from '../types/forum-post'

/**
 * Bấm một cảm xúc lên bài (CR-206, D-Q6: KHÔNG có chuông) — cùng kind là bỏ,
 * khác kind là đổi, backend phân xử và trả trạng thái chung cuộc.
 *
 * Không invalidate: một bài đang hiện ở ba chỗ (feed, tủ cá nhân, trang chi
 * tiết) — refetch cả ba là cuộn giật và tốn ba lượt gọi chỉ vì một cú bấm.
 * Backend đã trả số đếm từng cảm xúc chung cuộc, vá thẳng vào cache là đủ.
 */
export function useTogglePostReaction() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ postId, kind }: { postId: number; kind: number }) =>
      toggleForumPostReaction(postId, kind),
    onSuccess: (result, { postId }) => {
      const patch = (post: ForumPost): ForumPost =>
        post.id === postId
          ? {
              ...post,
              liked: result.liked,
              like_count: result.count,
              my_reaction: result.my_reaction,
              reactions: result.reactions,
            }
          : post

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
      // Dải ghim (F9a) cũng vẽ nút cảm xúc — thiếu nhánh này là bấm ở đó không nhúc nhích.
      queryClient.setQueryData<ForumPost[]>(queryKeys.forum.pinned(), (old) => old?.map(patch))
      // Hộp "ai đã bày tỏ cảm xúc" nếu đã từng mở thì dữ liệu vừa đổi — nạp lại lần mở sau.
      void queryClient.invalidateQueries({ queryKey: queryKeys.forum.postLikes(postId) })
    },
  })
}
