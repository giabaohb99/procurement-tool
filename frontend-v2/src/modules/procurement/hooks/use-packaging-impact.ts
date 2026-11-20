/**
 * duoc-CR-784 — dữ liệu màn Tác động giá bao bì: danh sách mã cho ô chọn + kết quả tính.
 *
 * `POST /impact` là đọc thuần (không ghi nhật ký) nên dùng `useQuery`: khóa là chính thân gửi đi, giữ
 * dữ liệu cũ khi đang tính lại để bảng không chớp trống mỗi lần đổi giá giả định.
 */
import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { fetchPackagingCodeOptions, fetchPackagingImpact } from '../api/packaging-cost-api'
import { packagingCostKeys } from '../config/packaging-cost-query-keys'
import type { PackagingImpactRequest } from '../types/packaging-cost-types'

export function usePackagingCodeOptions(enabled = true) {
  return useQuery({
    queryKey: packagingCostKeys.codeOptions(),
    queryFn: fetchPackagingCodeOptions,
    enabled,
    //  Danh mục định mức ít đổi; 5 phút là đủ, ghi báo giá / định mức sẽ tự dọn gốc.
    staleTime: 5 * 60 * 1000,
  })
}

export function usePackagingImpact(body: PackagingImpactRequest) {
  return useQuery({
    queryKey: packagingCostKeys.impact(body),
    queryFn: () => fetchPackagingImpact(body),
    enabled: body.codes.length > 0,
    placeholderData: keepPreviousData,
  })
}
