import { useMutation, useQueryClient } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'

import { createForumPost } from '../api/forum-api'
import type { NewForumPost } from '../types/forum-post'

/** Đăng bài mới rồi kéo mọi feed về trạng thái có bài đó ở đầu. */
export function useCreateForumPost() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (input: NewForumPost) => createForumPost(input),
    onSuccess: async () => {
      // reset (không phải invalidate) đưa useInfiniteQuery về đúng MỘT trang
      // đầu — bài mới nằm ngay dòng một; invalidate sẽ nạp lại lần lượt mọi
      // trang đã cuộn, vừa chậm vừa thừa.
      await queryClient.resetQueries({ queryKey: queryKeys.forum.feed() })
      await queryClient.resetQueries({ queryKey: queryKeys.forum.userPostsAll() })
      // F13b: thread mới phải hiện ngay trong box lẫn bộ đếm màn «Diễn đàn» —
      // khóa boards() là gốc của cả nhánh nên một lệnh quét đủ hai màn.
      await queryClient.invalidateQueries({ queryKey: queryKeys.forum.boards() })
    },
  })
}
