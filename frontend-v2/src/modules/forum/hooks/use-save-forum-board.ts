import { useMutation, useQueryClient } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'

import { createForumBoard, updateForumBoard } from '../api/forum-api'
import type { ForumBoardInput } from '../types/forum-admin'

/**
 * Tạo/sửa nhóm-box gộp một hook (CR-263) — `boardId = 0` là tạo mới. Backend
 * chỉ trả `{id}` nên không vá cache tại chỗ được, invalidate cả cây chuyên mục.
 */
export function useSaveForumBoard() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ boardId, input }: { boardId: number; input: ForumBoardInput }) =>
      boardId ? updateForumBoard(boardId, input) : createForumBoard(input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.forum.boards() })
    },
  })
}
