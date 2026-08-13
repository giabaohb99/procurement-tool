import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import {
  purchaseOrderPaymentApi,
  type PaymentRequestLine,
} from '../api/purchase-order-payment-api'

/** Công nợ của một đơn — chỉ nạp khi hộp thoại chọn hóa đơn được mở. */
export function usePurchaseOrderPayables(poCode: string, enabled: boolean) {
  return useQuery({
    queryKey: ['procurement', 'purchase-orders', poCode, 'payables'] as const,
    queryFn: () => purchaseOrderPaymentApi.listPayables(poCode),
    enabled: enabled && !!poCode,
  })
}

export function useCreatePaymentRequest() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: {
      request_date: string
      note: string
      payment_method: string
      lines: PaymentRequestLine[]
    }) => purchaseOrderPaymentApi.createPaymentRequest(payload),
    onSuccess: (requests) => {
      toast.success(`Đã tạo ${requests.length} phiếu yêu cầu thanh toán`)
      // Công nợ đổi theo -> nạp lại đơn (số "còn phải trả" nằm trên header).
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}
