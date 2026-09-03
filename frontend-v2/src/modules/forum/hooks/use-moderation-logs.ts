import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'

import { fetchForumModerationLogs } from '../api/forum-api'

/**
 * Nhật ký kiểm duyệt (CR-263) — chỉ tab «Quản trị» gọi, route đã gác quyền
 * nên không cần `enabled` theo `can()` ở đây.
 */
export function useModerationLogs(page: number) {
  return useQuery({
    queryKey: queryKeys.forum.moderationLogs(page),
    queryFn: () => fetchForumModerationLogs(page),
    placeholderData: keepPreviousData,
  })
}
