import { useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'

import { fetchForumSearchFilters } from '../api/forum-api'

/**
 * Tùy chọn hai ô lọc công ty/phòng ban của màn tìm kiếm (CR-263) — distinct
 * từ chính bảng bài viết nên người thường gọi được (không đụng danh mục
 * company/department vốn không có quyền đọc). Đổi rất chậm → cache 5 phút.
 */
export function useForumSearchFilters() {
  return useQuery({
    queryKey: queryKeys.forum.searchFilters(),
    queryFn: fetchForumSearchFilters,
    staleTime: 5 * 60 * 1000,
  })
}
