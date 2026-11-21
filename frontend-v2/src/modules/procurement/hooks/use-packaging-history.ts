/** duoc-CR-784 — tab Lịch sử mua hàng (phân trang + lọc + xếp tại máy chủ) và danh sách sản phẩm cho ô chọn. */
import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { fetchPackagingHhOptions, fetchPackagingHistory } from '../api/packaging-cost-api'
import { packagingCostKeys } from '../config/packaging-cost-query-keys'
import type { PackagingHistoryParams } from '../types/packaging-cost-types'

export function usePackagingHistory(params: PackagingHistoryParams) {
  return useQuery({
    queryKey: packagingCostKeys.history(params),
    queryFn: () => fetchPackagingHistory(params),
    placeholderData: keepPreviousData,
  })
}

/** Chỉ nạp khi đang ở chế độ "Theo mã sản phẩm" — chế độ mã VTBB không cần ~1.000 dòng định mức. */
export function usePackagingHhOptions(enabled: boolean) {
  return useQuery({
    queryKey: packagingCostKeys.hhOptions(),
    queryFn: fetchPackagingHhOptions,
    enabled,
    staleTime: 5 * 60 * 1000,
  })
}
