import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { appConfig } from '@/core/config/app-config'
import { queryKeys } from '@/shared/constants/query-keys'
import type { ListParams } from '@/shared/types/api'
import { payableApi } from '../api/payable-api'

/**
 * `keepPreviousData`: đổi trang / đổi bộ lọc thì giữ bảng cũ trên màn hình thay
 * vì nháy sang khung rỗng rồi vẽ lại.
 */
export function usePayables(params: ListParams = {}) {
  const query: ListParams = { page: 1, page_size: appConfig.defaultPageSize, ...params }
  return useQuery({
    queryKey: queryKeys.finance.payables(query),
    queryFn: () => payableApi.list(query),
    placeholderData: keepPreviousData,
  })
}

/**
 * Bốn số tổng ở đầu trang. Nhận ĐÚNG bộ lọc của bảng nhưng BỎ phân trang: tổng
 * phải tính trên cả tập kết quả, không phải trên 20 dòng đang hiện.
 */
export function usePayableSummary(params: ListParams = {}) {
  return useQuery({
    queryKey: queryKeys.finance.payableSummary(params),
    queryFn: () => payableApi.summary(params),
    placeholderData: keepPreviousData,
  })
}
