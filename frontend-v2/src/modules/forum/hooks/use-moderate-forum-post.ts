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
      // Ẩn/gỡ bài đang ghim làm bài rời (hoặc quay lại) dải Thông báo (F9a).
      await queryClient.invalidateQueries({ queryKey: queryKeys.forum.pinned() })
      // Thread trong box ẩn/khôi phục cũng phải biến mất / hiện lại ở trang
      // thread (bao-CR-276). API trả null, không biết box nào — quét gốc `boards`.
      await queryClient.invalidateQueries({ queryKey: queryKeys.forum.boards() })
      // Kiểm duyệt ngay trên kết quả tìm kiếm (CR-263): trạng thái đổi thì mọi
      // trang kết quả đang cache đều cũ — invalidate cả cụm theo tiền tố, và
      // nhật ký kiểm duyệt vừa có thêm dòng mới.
      await queryClient.invalidateQueries({ queryKey: queryKeys.forum.searchAll() })
      await queryClient.invalidateQueries({ queryKey: queryKeys.forum.moderationLogsAll() })
    },
  })
}
