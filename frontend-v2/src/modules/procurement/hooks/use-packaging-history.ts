/**
 * duoc-CR-784 — tab Lịch sử mua hàng (phân trang + lọc + xếp tại máy chủ) và danh sách sản phẩm cho ô chọn.
 *
 * bao-CR-801 — cùng khuôn cho Lịch sử mua nguyên liệu (`rawMaterial`): danh sách đi đường `material-history`, ô chọn mã đi
 * `material-code-options` (khóa `packaging_material_price`). Mỗi màn chỉ BẬT truy vấn của nguồn mình: màn nguyên liệu không
 * gọi `history` / `code-options` / `fg-options` của VTBB (người chỉ giữ khóa nguyên liệu gặp 403), và ngược lại.
 */
import { useMemo } from 'react'
import { keepPreviousData, useQuery } from '@tanstack/react-query'

import {
  fetchPackagingFgOptions,
  fetchPackagingHistory,
  fetchPackagingMaterialHistory,
} from '../api/packaging-cost-api'
import { packagingCostKeys } from '../config/packaging-cost-query-keys'
import type { PackagingCodeOption, PackagingHistoryParams } from '../types/packaging-cost-types'
import { sortPackagingCodeOptions } from '../utils/packaging-code-match'
import { toMaterialHistoryParams } from '../utils/packaging-history'
import { usePackagingCodeOptions } from './use-packaging-impact'
import { usePackagingMaterialCodeOptions } from './use-packaging-material-price-list'

export function usePackagingHistory(params: PackagingHistoryParams, rawMaterial = false) {
  return useQuery({
    queryKey: rawMaterial
      ? packagingCostKeys.materialHistory(toMaterialHistoryParams(params))
      : packagingCostKeys.history(params),
    queryFn: () =>
      rawMaterial
        ? fetchPackagingMaterialHistory(toMaterialHistoryParams(params))
        : fetchPackagingHistory(params),
    placeholderData: keepPreviousData,
  })
}

/** Chỉ nạp khi đang ở chế độ "Theo mã sản phẩm" — chế độ mã VTBB không cần ~1.000 dòng định mức. */
export function usePackagingFgOptions(enabled: boolean) {
  return useQuery({
    queryKey: packagingCostKeys.fgOptions(),
    queryFn: fetchPackagingFgOptions,
    enabled,
    staleTime: 5 * 60 * 1000,
  })
}

/**
 * Danh sách cho hai ô chọn của màn lịch sử. VTBB: mọi mã có trong sổ giá (27/11/2026, tìm được cả theo tên NCC — như Giá mua
 * gần nhất / Bảng giá) + sản phẩm có định mức khi ở chế độ sản phẩm. Nguyên liệu: mọi mã nguyên liệu đã có giá, không có
 * danh sách sản phẩm.
 */
export function usePackagingHistoryOptions(rawMaterial: boolean, productMode: boolean) {
  const packagingQuery = usePackagingCodeOptions(!rawMaterial, 'all')
  const materialQuery = usePackagingMaterialCodeOptions(rawMaterial)
  const fgQuery = usePackagingFgOptions(!rawMaterial && productMode)
  const codeQuery = rawMaterial ? materialQuery : packagingQuery
  const codeOptions = useMemo(() => sortPackagingCodeOptions(codeQuery.data ?? []), [codeQuery.data])
  const productOptions = useMemo<PackagingCodeOption[]>(
    () => (fgQuery.data ?? []).map((item) => ({ ...item, group: '', usage: 0, new: null })),
    [fgQuery.data],
  )
  return {
    codeOptions,
    productOptions,
    loading: !rawMaterial && productMode ? fgQuery.isLoading : codeQuery.isLoading,
  }
}
