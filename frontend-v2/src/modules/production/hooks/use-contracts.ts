import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { appConfig } from '@/core/config/app-config'
import { queryKeys } from '@/shared/constants/query-keys'
import type { ListParams } from '@/shared/types/api'
import { contractApi } from '../api/contract-api'

/**
 * Danh sách hợp đồng có phân trang.
 *
 * `enabled`: backend chặn `contract.read`, không có quyền mà vẫn gọi thì người
 * dùng ăn một toast 403 ngay khi mở tab — thà đừng gọi.
 */
export function useContracts(params: ListParams = {}, options: { enabled?: boolean } = {}) {
  const query: ListParams = {
    page: 1,
    page_size: appConfig.defaultPageSize,
    ...params,
  }

  return useQuery({
    queryKey: queryKeys.production.contracts(query),
    queryFn: () => contractApi.list(query),
    placeholderData: keepPreviousData,
    enabled: options.enabled ?? true,
  })
}
