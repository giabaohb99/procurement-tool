import { useMutation, useQueryClient } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'

import { pinForumPost, unpinForumPost } from '../api/forum-api'
import { patchPostInCaches } from '../utils/patch-post-caches'

/**
 * Ghim / bỏ ghim của quản trị viên (F9a/CR-199). Backend trả nguyên PostOut
 * sau thao tác nên vá thẳng cache (nhãn ghim đổi ngay, không F5); riêng danh
 * sách dải ghim thì invalidate — ghim/bỏ ghim là THÊM/BỚT phần tử, không phải
 * sửa tại chỗ.
 */
export function usePinForumPost() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ postId, pinned }: { postId: number; pinned: boolean }) =>
      pinned ? pinForumPost(postId) : unpinForumPost(postId),
    onSuccess: (post) => {
      patchPostInCaches(queryClient, post)
      void queryClient.invalidateQueries({ queryKey: queryKeys.forum.pinned() })
    },
  })
}
