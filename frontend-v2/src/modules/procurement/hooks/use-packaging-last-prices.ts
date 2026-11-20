/** duoc-CR-784 — tab Giá mua gần nhất (phân trang + lọc + xếp tại máy chủ). */
import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { fetchPackagingLastPrices } from '../api/packaging-cost-api'
import { packagingCostKeys } from '../config/packaging-cost-query-keys'
import type { PackagingLastPricesParams } from '../types/packaging-cost-types'

export function usePackagingLastPrices(params: PackagingLastPricesParams) {
  return useQuery({
    queryKey: packagingCostKeys.lastPrices(params),
    queryFn: () => fetchPackagingLastPrices(params),
    placeholderData: keepPreviousData,
  })
}
