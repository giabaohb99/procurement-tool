/** duoc-CR-784 — tab Tổng hợp theo sản phẩm (lọc + xếp + phân trang tại máy chủ). */
import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { fetchPackagingProductOverview } from '../api/packaging-cost-api'
import { packagingCostKeys } from '../config/packaging-cost-query-keys'
import type { PackagingOverviewParams } from '../types/packaging-cost-types'

export function usePackagingProductOverview(params: PackagingOverviewParams) {
  return useQuery({
    queryKey: packagingCostKeys.productOverview(params),
    queryFn: () => fetchPackagingProductOverview(params),
    //  Giữ số đếm + dòng cũ trong lúc đổi bộ lọc / trang để chip và bảng không chớp trống.
    placeholderData: keepPreviousData,
  })
}
