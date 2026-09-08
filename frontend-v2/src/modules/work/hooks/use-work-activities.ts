import { useInfiniteQuery, useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'
import { workActivityApi } from '../api/work-activity-api'

/** Số dòng mỗi lượt lấy — cỡ một màn hình rưỡi, đủ để cuộn thấy còn nữa. */
export const ACTIVITY_PAGE_SIZE = 30

interface ActivityFilter {
  kind?: number | null
  by?: number | null
}

/**
 * Dòng hoạt động của một dự án, mới nhất trước, lấy thêm khi cuộn (§8).
 *
 * Trang tính bằng `offset` chứ không con trỏ: backend sắp theo `id` giảm dần và
 * `id` là số tự tăng, nên dòng mới sinh ra trong lúc đang cuộn chỉ chen vào ĐẦU
 * — không đẩy lệch các trang đã lấy.
 */
export function useWorkActivities(listId: number, filter: ActivityFilter = {}) {
  const params = { kind: filter.kind ?? null, by: filter.by ?? null }
  return useInfiniteQuery({
    queryKey: queryKeys.work.activities(listId, params),
    queryFn: ({ pageParam }) =>
      workActivityApi.list(listId, { ...params, offset: pageParam, limit: ACTIVITY_PAGE_SIZE }),
    initialPageParam: 0,
    getNextPageParam: (last, pages) =>
      last.has_more ? pages.reduce((n, p) => n + p.items.length, 0) : undefined,
    enabled: listId > 0,
  })
}

/** Người từng thao tác trên dự án — nguồn cho ô lọc «theo người». */
export function useWorkActivityActors(listId: number) {
  return useQuery({
    queryKey: queryKeys.work.activityActors(listId),
    queryFn: () => workActivityApi.actors(listId),
    enabled: listId > 0,
  })
}
