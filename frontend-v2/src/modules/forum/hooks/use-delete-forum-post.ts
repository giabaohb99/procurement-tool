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
    },
  })
}
