import { useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'

import { fetchForumFeed } from '../api/forum-api'

/**
 * Thăm dò "có bài viết mới không": mỗi 45 giây hỏi đúng MỘT bài mới nhất rồi so
 * id với bài mới nhất đang hiện. Rẻ hơn nạp lại cả feed, và không đụng cache
 * của feed (khóa riêng `feedHead`).
 *
 * Trả về `true` khi máy chủ đã có bài mới hơn màn hình — feed hiện nút
 * "Có bài viết mới".
 */
export function useNewPostSignal(newestVisibleId: number | undefined): boolean {
  const head = useQuery({
    queryKey: queryKeys.forum.feedHead(),
    queryFn: () => fetchForumFeed(0, 1),
    refetchInterval: 45_000,
    // Feed còn trống thì chưa có gì để so — khỏi thăm dò.
    enabled: newestVisibleId !== undefined,
  })
  const headId = head.data?.items[0]?.id ?? 0
  return newestVisibleId !== undefined && headId > newestVisibleId
}
