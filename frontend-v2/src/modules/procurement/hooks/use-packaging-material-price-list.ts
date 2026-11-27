/**
 * bao-CR-800 — dữ liệu màn Bảng giá nguyên liệu: danh sách (phân trang + xếp tại máy chủ) và danh sách mã cho ô chọn mã.
 * Cả hai đi đường RIÊNG của nguyên liệu (khóa `packaging_material_price`), không đụng đường của Bảng giá VTBB.
 */
import { keepPreviousData, useQuery } from '@tanstack/react-query'

import {
  fetchPackagingMaterialCodeOptions,
  fetchPackagingMaterialPriceList,
} from '../api/packaging-cost-api'
import { packagingCostKeys } from '../config/packaging-cost-query-keys'
import type { PackagingMaterialPriceListParams } from '../types/packaging-cost-types'

export function usePackagingMaterialPriceList(params: PackagingMaterialPriceListParams) {
  return useQuery({
    queryKey: packagingCostKeys.materialPriceList(params),
    queryFn: () => fetchPackagingMaterialPriceList(params),
    placeholderData: keepPreviousData,
  })
}

export function usePackagingMaterialCodeOptions() {
  return useQuery({
    queryKey: packagingCostKeys.materialCodeOptions(),
    queryFn: fetchPackagingMaterialCodeOptions,
    //  Danh mục nguyên liệu có giá ít đổi; 5 phút là đủ (cùng nhịp với ô chọn mã VTBB).
    staleTime: 5 * 60 * 1000,
  })
}
