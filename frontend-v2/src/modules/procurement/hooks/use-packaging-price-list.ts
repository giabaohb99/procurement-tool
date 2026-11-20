/** duoc-CR-784 — Bảng giá VTBB (phân trang + xếp tại máy chủ) và ngưỡng giá từng mã. */
import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import {
  fetchPackagingPriceLimit,
  fetchPackagingPriceList,
  savePackagingPriceLimit,
  type PackagingPriceLimitPayload,
} from '../api/packaging-cost-api'
import { packagingCostKeys } from '../config/packaging-cost-query-keys'
import type { PackagingPriceListParams } from '../types/packaging-cost-types'

export function usePackagingPriceList(params: PackagingPriceListParams) {
  return useQuery({
    queryKey: packagingCostKeys.priceList(params),
    queryFn: () => fetchPackagingPriceList(params),
    placeholderData: keepPreviousData,
  })
}

/** Ngưỡng của một mã — chỉ nạp khi hộp thoại mở (`code` rỗng = tắt). */
export function usePackagingPriceLimit(code: string) {
  return useQuery({
    queryKey: packagingCostKeys.limit(code),
    queryFn: () => fetchPackagingPriceLimit(code),
    enabled: Boolean(code),
  })
}

export function useSavePackagingPriceLimit() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: number | null; payload: PackagingPriceLimitPayload }) =>
      savePackagingPriceLimit(id, payload),
    onSuccess: (_data, { payload }) => {
      toast.success(`Đã lưu ngưỡng giá ${payload.product_code}`)
      //  Ngưỡng hiện ở cả Bảng giá lẫn bảng mã đã chọn của màn Tác động — dọn cả gốc.
      void queryClient.invalidateQueries({ queryKey: packagingCostKeys.all })
    },
  })
}
