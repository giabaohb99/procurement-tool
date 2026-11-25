/** duoc-CR-784 — Bảng giá VTBB (phân trang + xếp tại máy chủ). Ngưỡng sàn / trần đã bỏ ở phase 04. */
import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { fetchPackagingPriceList } from '../api/packaging-cost-api'
import { packagingCostKeys } from '../config/packaging-cost-query-keys'
import type { PackagingPriceListParams } from '../types/packaging-cost-types'

export function usePackagingPriceList(params: PackagingPriceListParams) {
  return useQuery({
    queryKey: packagingCostKeys.priceList(params),
    queryFn: () => fetchPackagingPriceList(params),
    placeholderData: keepPreviousData,
  })
}
