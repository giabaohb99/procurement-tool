import { useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'

import { fetchForumBoards } from '../api/forum-api'

/** Cây nhóm → box của tab «Diễn đàn» (F13b) — nạp một lần, cả cây nhẹ. */
export function useForumBoards() {
  return useQuery({
    queryKey: queryKeys.forum.boards(),
    queryFn: fetchForumBoards,
  })
}
