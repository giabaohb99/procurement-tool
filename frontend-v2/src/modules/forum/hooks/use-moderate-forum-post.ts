import { useMutation, useQueryClient } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'

import { hideForumPost, removeForumPost, restoreForumPost } from '../api/forum-api'

export type ModerationAction = 'hide' | 'restore' | 'remove'

interface ModerateInput {
  postId: number
  action: ModerationAction
  /** Bắt buộc với hide/remove (QĐ-D1) — hộp thoại đã chặn trước, backend chặn sau. */
  reason?: string
}

/**
 * Ẩn / khôi phục / xóa bài của quản trị viên (F5). Xong thì reset cả cụm feed
 * + tủ bài cá nhân + trang chi tiết — trạng thái bài đổi làm bài xuất hiện/biến
 * mất ở nhiều mắt khác nhau, vá cache từng trang không đáng công.
 */
export function useModerateForumPost() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ postId, action, reason = '' }: ModerateInput) => {
      if (action === 'hide') return hideForumPost(postId, reason)
      if (action === 'remove') return removeForumPost(postId, reason)
      return restoreForumPost(postId)
    },
    onSuccess: async (_data, { postId }) => {
      await queryClient.resetQueries({ queryKey: queryKeys.forum.feed() })
      await queryClient.resetQueries({ queryKey: queryKeys.forum.userPostsAll() })
      await queryClient.invalidateQueries({ queryKey: queryKeys.forum.post(postId) })
    },
  })
}
