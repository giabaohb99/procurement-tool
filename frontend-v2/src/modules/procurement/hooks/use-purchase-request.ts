import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import {
  purchaseRequestApi,
  type PurchaseRequestPayload,
} from '../api/purchase-request-api'

/** Một phiếu YCMH. `id <= 0` (màn tạo mới) thì không gọi API. */
export function usePurchaseRequest(id: number) {
  return useQuery({
    queryKey: queryKeys.procurement.purchaseRequest(id),
    queryFn: () => purchaseRequestApi.getById(id),
    enabled: id > 0,
  })
}

/** Số lượng đã đặt theo mã hàng — để cột "Đã đặt" trên bảng dòng hàng. */
export function useOrderProgress(id: number) {
  return useQuery({
    queryKey: queryKeys.procurement.purchaseRequestProgress(id),
    queryFn: () => purchaseRequestApi.getOrderProgress(id),
    enabled: id > 0,
  })
}

/** Tạo mới HOẶC cập nhật — hai màn dùng chung một form nên gộp một hook. */
export function useSavePurchaseRequest() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, payload }: { id?: number; payload: PurchaseRequestPayload }) =>
      id ? purchaseRequestApi.update(id, payload) : purchaseRequestApi.create(payload),
    onSuccess: (_data, variables) => {
      toast.success(variables.id ? 'Đã lưu phiếu' : 'Đã tạo phiếu')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

/** Tên thao tác chuyển trạng thái + câu báo thành công tương ứng. */
const ACTION_LABELS = {
  submit: 'Đã gửi duyệt',
  approve: 'Đã duyệt phiếu',
  dispatch: 'Đã điều phối',
  complete: 'Đã hoàn thành phiếu',
  reject: 'Đã trả lại phiếu',
  cancel: 'Đã từ chối phiếu',
  return: 'Đã trả phiếu về cho người yêu cầu',
  copy: 'Đã nhân bản phiếu',
} as const

export type PurchaseRequestAction = keyof typeof ACTION_LABELS

/**
 * Mọi thao tác chuyển trạng thái gom vào MỘT mutation: chúng chỉ khác nhau ở
 * đường dẫn và câu thông báo, tách tám hook chỉ tổ lặp code.
 *
 * `reason` bắt buộc với reject / cancel / return (backend cũng chặn).
 */
export function usePurchaseRequestAction(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ action, reason }: { action: PurchaseRequestAction; reason?: string }) => {
      switch (action) {
        case 'submit':
          return purchaseRequestApi.submit(id)
        case 'approve':
          return purchaseRequestApi.approve(id)
        case 'dispatch':
          return purchaseRequestApi.dispatch(id)
        case 'complete':
          return purchaseRequestApi.complete(id)
        case 'reject':
          return purchaseRequestApi.reject(id, reason ?? '')
        case 'cancel':
          return purchaseRequestApi.cancel(id, reason ?? '')
        case 'return':
          return purchaseRequestApi.returnToRequester(id, reason ?? '')
        case 'copy':
          return purchaseRequestApi.copy(id)
      }
    },
    onSuccess: (_data, variables) => {
      toast.success(ACTION_LABELS[variables.action])
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

export function useDeletePurchaseRequest() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => purchaseRequestApi.remove(id),
    onSuccess: () => {
      toast.success('Đã xóa phiếu')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

/** Gán NSTM phụ trách cho một dòng. */
export function useAssignPurchaser(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (item: { id: number; assignee: string }) =>
      purchaseRequestApi.assign(id, [item]),
    onSuccess: () => {
      toast.success('Đã cập nhật NSTM phụ trách')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

/** Cập nhật tiến độ một dòng hàng. */
export function useUpdateItemStatus(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (item: {
      id: number
      line_status: string
      progress_note?: string
      note?: string
      expected_date?: string
      expected_date_reason?: string
    }) => purchaseRequestApi.updateItemStatus(id, [item]),
    onSuccess: () => {
      toast.success('Đã cập nhật tiến độ dòng')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

export function useSetUrgent(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (isUrgent: boolean) => purchaseRequestApi.setUrgent(id, isUrgent),
    onSuccess: () => {
      toast.success('Đã cập nhật Đơn gấp')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}
