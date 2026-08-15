import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { appConfig } from '@/core/config/app-config'
import { queryKeys } from '@/shared/constants/query-keys'
import type { ListParams } from '@/shared/types/api'
import { supplierApi } from '../api/supplier-api'

/**
 * Danh sách nhà cung cấp có phân trang + tìm kiếm.
 * `placeholderData: keepPreviousData` giữ nguyên bảng cũ trong lúc nạp trang mới,
 * tránh bảng nháy trắng mỗi lần bấm sang trang.
 */
export function useSuppliers(
  params: ListParams = {},
  options: { enabled?: boolean } = {},
) {
  const query: ListParams = {
    page: 1,
    page_size: appConfig.defaultPageSize,
    ...params,
  }

  return useQuery({
    queryKey: queryKeys.production.suppliers(query),
    queryFn: () => supplierApi.list(query),
    placeholderData: keepPreviousData,
    // Không có quyền đọc `supplier` thì đừng gọi API cho backend trả 403.
    enabled: options.enabled ?? true,
  })
}
