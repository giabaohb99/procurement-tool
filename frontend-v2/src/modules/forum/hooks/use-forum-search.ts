import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'

import { searchForumPosts } from '../api/forum-api'
import type { ForumSearchParams } from '../types/forum-post'

/**
 * Một trang kết quả tìm bài (CR-263). `enabled` do màn quyết — chỉ chạy khi
 * người dùng đã bấm Tìm (có bộ lọc thật), không tự quét cả diễn đàn lúc mở
 * trang. `placeholderData` giữ trang cũ khi lật trang, khỏi nháy skeleton.
 */
export function useForumSearch(params: ForumSearchParams, enabled: boolean) {
  // why: key phải là object KHÔNG chứa undefined — hai bộ lọc "rỗng" viết khác
  // nhau (thiếu key vs key=undefined) mà cùng nghĩa thì cache sẽ tách đôi.
  const keyParams: Record<string, string | number> = {
    q: params.q || '',
    author_q: params.author_q || '',
    company_id: params.company_id || 0,
    dept_id: params.dept_id || 0,
    status: params.status || 0,
    page: params.page || 1,
  }
  return useQuery({
    queryKey: queryKeys.forum.search(keyParams),
    queryFn: () => searchForumPosts(params),
    enabled,
    placeholderData: keepPreviousData,
  })
}
