import { useMutation, useQueryClient } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'

import { updateForumPost } from '../api/forum-api'
import type { ForumPostPatch } from '../types/forum-post'
import { patchPostInCaches } from '../utils/patch-post-caches'

/**
 * Sửa bài (bao-CR-707). Backend trả nguyên PostOut nên vá thẳng cache bài lẻ +
 * các feed; chuyển box / đổi nhãn còn làm đổi danh sách box, kết quả tìm kiếm,
 * dải ghim và nhật ký kiểm duyệt — quét các gốc đó thay vì đoán chỗ nào lệch.
 */
export function useUpdateForumPost() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ postId, patch }: { postId: number; patch: ForumPostPatch }) =>
      updateForumPost(postId, patch),
    onSuccess: (post) => {
      patchPostInCaches(queryClient, post)
      void queryClient.invalidateQueries({ queryKey: queryKeys.forum.boards() })
      void queryClient.invalidateQueries({ queryKey: queryKeys.forum.searchAll() })
      void queryClient.invalidateQueries({ queryKey: queryKeys.forum.pinned() })
      void queryClient.invalidateQueries({ queryKey: queryKeys.forum.moderationLogsAll() })
    },
  })
}
