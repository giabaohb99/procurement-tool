import { useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'
import type { ListParams } from '@/shared/types/api'
import { sealTypeApi } from '../api/seal-type-api'

/**
 * Danh mục Loại con dấu để đổ vào ô chọn trên form tạo phiếu. Danh mục đổi thưa
 * nên giữ cache 5 phút. `enabled` cho phép tắt khi thiếu quyền `seal_type.read`.
 */
export function useSealTypes(params: ListParams = {}, options: { enabled?: boolean } = {}) {
  const query: ListParams = { page: 1, page_size: 200, ...params }
  return useQuery({
    queryKey: queryKeys.sealType.list(query),
    queryFn: () => sealTypeApi.list(query),
    staleTime: 5 * 60 * 1000,
    enabled: options.enabled ?? true,
  })
}
