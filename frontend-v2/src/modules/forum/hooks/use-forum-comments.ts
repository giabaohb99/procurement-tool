import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'

import {
  createPostComment,
  deletePostComment,
  fetchPostComments,
  toggleCommentLike,
  uploadCommentFiles,
} from '../api/forum-comment-api'
import { refreshPostInCaches } from '../utils/patch-post-caches'

/** Trang bình luận gốc MỚI NHẤT của một bài; trang cũ hơn tải tay qua `fetchPostComments`. */
export function useForumComments(postId: number) {
  return useQuery({
    queryKey: queryKeys.forum.comments(postId),
    queryFn: () => fetchPostComments(postId),
    enabled: postId > 0,
  })
}

export function useCreateForumComment(postId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({
      body,
      parentId = 0,
      files = [],
    }: {
      body: string
      parentId?: number
      files?: File[]
    }) => {
      const uploaded = files.length ? await uploadCommentFiles(files) : []
      return createPostComment(
        postId,
        body,
        parentId,
        uploaded.map((file) => file.file_id),
      )
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.forum.comments(postId) })
      // Số "N bình luận" dưới bài lấy từ PostOut — vá lại bài vào MỌI cache.
      void refreshPostInCaches(queryClient, postId)
    },
  })
}

/** Thích / xóa một bình luận GỐC — phản hồi nằm trong state cục bộ, xử lý tại chỗ. */
export function useForumCommentActions(postId: number) {
  const queryClient = useQueryClient()

  const toggleLike = useMutation({
    mutationFn: toggleCommentLike,
    onSuccess: () =>
      void queryClient.invalidateQueries({ queryKey: queryKeys.forum.comments(postId) }),
  })
  const remove = useMutation({
    mutationFn: deletePostComment,
    onSuccess: () => {
      toast.success('Đã xóa bình luận')
      void queryClient.invalidateQueries({ queryKey: queryKeys.forum.comments(postId) })
      void refreshPostInCaches(queryClient, postId)
    },
  })

  return { toggleLike, remove }
}
