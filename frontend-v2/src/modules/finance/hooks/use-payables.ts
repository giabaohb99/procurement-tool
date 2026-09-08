import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

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
export function usePayableSummary(params: ListParams = {}, options: { enabled?: boolean } = {}) {
  return useQuery({
    queryKey: queryKeys.finance.payableSummary(params),
    queryFn: () => payableApi.summary(params),
    placeholderData: keepPreviousData,
    // Trang Tổng quan mượn số này nên phải tắt được: không có `payable.read`
    // thì gọi chỉ để nhận 403.
    enabled: options.enabled ?? true,
  })
}

/**
 * CR-268 — cấn trừ tiền treo cấp NCC vào một khoản công nợ (kế toán bấm tay).
 * Đổi số cả Công nợ lẫn tiền treo -> làm mất hiệu lực toàn nhánh `finance`.
 */
export function useOffsetPrepay() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ payableId, amount }: { payableId: number; amount: number }) =>
      payableApi.offsetPrepay(payableId, amount),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.finance.all })
      toast.success('Đã cấn trừ tiền treo vào khoản công nợ')
    },
  })
}
