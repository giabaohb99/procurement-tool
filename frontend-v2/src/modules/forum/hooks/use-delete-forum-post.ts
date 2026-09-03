import { useMutation, useQueryClient } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'

import { deleteForumPost } from '../api/forum-api'

/** Xóa bài của chính mình rồi rút bài đó khỏi mọi feed đang mở. */
export function useDeleteForumPost() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => deleteForumPost(id),
    onSuccess: async () => {
      await queryClient.resetQueries({ queryKey: queryKeys.forum.feed() })
      await queryClient.resetQueries({ queryKey: queryKeys.forum.userPostsAll() })
      // Bài đang ghim mà tác giả tự xóa thì cũng phải rời dải Thông báo (F9a).
      await queryClient.invalidateQueries({ queryKey: queryKeys.forum.pinned() })
      // Thread trong box cũng phải rời trang thread (bao-CR-276). API xóa trả
      // null nên không biết bài thuộc box nào — quét gốc `boards` luôn, không
      // gạn theo board_id như hook ghim được.
      await queryClient.invalidateQueries({ queryKey: queryKeys.forum.boards() })
    },
  })
}
