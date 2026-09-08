import { useMutation, useQueryClient } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'

import { deleteForumBoard } from '../api/forum-api'

/** Xóa nhóm/box RỖNG (CR-263) — còn bài/box con thì backend 400, toast lý do. */
export function useDeleteForumBoard() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (boardId: number) => deleteForumBoard(boardId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.forum.boards() })
    },
  })
}
