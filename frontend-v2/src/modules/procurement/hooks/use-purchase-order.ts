import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import {
  purchaseOrderApi,
  type PurchaseOrderPayload,
  type PurchaseOrderPriceAdjustPayload,
} from '../api/purchase-order-api'

/** Một ĐMH. `id <= 0` (màn tạo mới) thì không gọi API. */
export function usePurchaseOrder(id: number) {
  return useQuery({
    queryKey: queryKeys.procurement.purchaseOrder(id),
    queryFn: () => purchaseOrderApi.getById(id),
    enabled: id > 0,
  })
}

/** Dữ liệu bản in (kèm hồ sơ công ty / NCC / kho). */
export function usePurchaseOrderPrintData(id: number) {
  return useQuery({
    queryKey: [...queryKeys.procurement.purchaseOrder(id), 'print'] as const,
    queryFn: () => purchaseOrderApi.getPrintData(id),
    enabled: id > 0,
  })
}

/**
 * duoc-CR-777 — dữ liệu "Mẫu thu mua" cho bản in YCMH mở từ đơn. Lệnh gọi PHỤ: hỏng (403/404 khi
 * ngoài quyền / phạm vi) thì trang chỉ giấu hai mẫu thu mua, không báo lỗi — GET vốn không toast,
 * và 4xx không thử lại (cấu hình chung của `queryClient`).
 */
export function usePurchaseOrderPurchasingPrint(id: number, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.procurement.purchaseOrderPurchasingPrint(id),
    queryFn: () => purchaseOrderApi.getPurchasingPrint(id),
    enabled: enabled && id > 0,
  })
}

/** Tạo mới HOẶC cập nhật — hai màn dùng chung một form nên gộp một hook. */
export function useSavePurchaseOrder() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, payload }: { id?: number; payload: PurchaseOrderPayload }) =>
      id ? purchaseOrderApi.update(id, payload) : purchaseOrderApi.create(payload),
    onSuccess: (_data, variables) => {
      toast.success(variables.id ? 'Đã lưu đơn mua hàng' : 'Đã tạo đơn mua hàng')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

const ACTION_LABELS = {
  submit: 'Đã gửi duyệt',
  approve: 'Đã duyệt đơn',
  complete: 'Đã hoàn thành đơn',
  reopen: 'Đã mở lại đơn',
  reject: 'Đã từ chối đơn',
  return: 'Đã trả đơn về cho người tạo',
  unapprove: 'Đã hủy duyệt — đơn về Nháp',
  cancel: 'Đã hủy đơn',
  copy: 'Đã nhân bản thành đơn nháp mới',
} as const

export type PurchaseOrderAction = keyof typeof ACTION_LABELS

/**
 * Mọi thao tác chuyển trạng thái gom vào MỘT mutation — chúng chỉ khác đường
 * dẫn và câu thông báo. `reason` bắt buộc với reject / return / unapprove / cancel.
 */
export function usePurchaseOrderAction(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ action, reason }: { action: PurchaseOrderAction; reason?: string }) => {
      switch (action) {
        case 'submit':
          return purchaseOrderApi.submit(id)
        case 'approve':
          return purchaseOrderApi.approve(id)
        case 'complete':
          return purchaseOrderApi.complete(id)
        case 'reopen':
          return purchaseOrderApi.reopen(id)
        case 'reject':
          return purchaseOrderApi.reject(id, reason ?? '')
        case 'return':
          return purchaseOrderApi.returnToCreator(id, reason ?? '')
        case 'unapprove':
          return purchaseOrderApi.unapprove(id, reason ?? '')
        case 'cancel':
          return purchaseOrderApi.cancel(id, reason ?? '')
        case 'copy':
          return purchaseOrderApi.copy(id)
      }
    },
    onSuccess: (_data, variables) => {
      toast.success(ACTION_LABELS[variables.action])
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

/**
 * bao-CR-794 — Sửa giá sau duyệt. Thông báo thành công là NGUYÊN câu `message` của máy chủ (câu
 * đó nhắc cả YCTT đang Nháp cần kiểm lại số tiền); lỗi thì `http-client` đã tự bật thông báo.
 */
export function useAdjustPurchaseOrderPrices(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: PurchaseOrderPriceAdjustPayload) =>
      purchaseOrderApi.adjustPrices(id, payload),
    onSuccess: (result) => {
      toast.success(result.message || 'Đã sửa giá')
      //  Máy chủ trả luôn chi tiết đơn mới: ghi thẳng vào cache để màn hình có giá mới ngay, không
      //  hở một nhịp chờ nạp lại mà người dùng bấm Lưu đơn kèm giá cũ.
      queryClient.setQueryData(queryKeys.procurement.purchaseOrder(id), result.order)
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

export function useDeletePurchaseOrder() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => purchaseOrderApi.remove(id),
    onSuccess: () => {
      toast.success('Đã xóa đơn mua hàng')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

/** Tình trạng hồ sơ chứng từ (cập nhật tay). */
export function useSetDocumentStatus(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (documentStatus: string) =>
      purchaseOrderApi.setDocumentStatus(id, documentStatus),
    onSuccess: () => {
      toast.success('Đã cập nhật hồ sơ chứng từ')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

/** Đổi tiến độ một dòng hàng (backend tự kiểm tra điều kiện chuyển bước). */
export function useSetItemProgress(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      itemId,
      status,
      reason,
    }: {
      itemId: number
      status: string
      reason?: string
    }) => purchaseOrderApi.setItemProgress(id, itemId, status, reason ?? ''),
    onSuccess: () => {
      toast.success('Đã cập nhật tiến độ dòng')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}
