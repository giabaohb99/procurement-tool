import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'

import { fetchBoardThreads } from '../api/forum-api'

/**
 * Một trang thread của box (F13b) — phân trang số trang. `placeholderData`
 * giữ trang cũ trên màn trong lúc trang mới đang tải, khỏi nháy skeleton
 * mỗi lần bấm số trang.
 */
export function useBoardThreads(boardId: number, page: number) {
  return useQuery({
    queryKey: queryKeys.forum.boardThreads(boardId, page),
    queryFn: () => fetchBoardThreads(boardId, page),
    enabled: Number.isFinite(boardId) && boardId > 0,
    placeholderData: keepPreviousData,
  })
}
