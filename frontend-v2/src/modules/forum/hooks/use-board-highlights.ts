import { useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'

import { fetchBoardHighlights } from '../api/forum-api'

/** Hai khối máy tự xếp của sidebar «Diễn đàn» (F13c) — «Nổi bật» đi `usePinnedPosts`. */
export function useBoardHighlights() {
  return useQuery({
    queryKey: queryKeys.forum.boardHighlights(),
    queryFn: fetchBoardHighlights,
  })
}
