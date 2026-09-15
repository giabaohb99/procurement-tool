import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'

import { purchaseRequestOptionApi } from '../api/purchase-request-option-api'
import type {
  AvailablePrSurveyLinesParams,
  PrAssignSupplierPayload,
  PrOptionManualPayload,
  PrOptionSupplierPayload,
  PrOptionUpdatePayload,
} from '../types/purchase-request-options'

/**
 * Hooks màn XỬ LÝ PHƯƠNG ÁN của YCMH (bao-CR-310).
 *
 * Mọi mutation invalidate cả nhánh `procurement` — phương án đổi thì
 * `option_count` / `chosen_option` trong chi tiết phiếu cũng phải tươi theo.
 */

/** Phương án của MỘT dòng hàng. `retry: false` vì 403/404 thử lại cũng vậy. */
export function usePurchaseRequestItemOptions(prId: number, itemId: number) {
  return useQuery({
    queryKey: queryKeys.procurement.purchaseRequestItemOptions(prId, itemId),
    queryFn: () => purchaseRequestOptionApi.listOptions(prId, itemId),
    enabled: prId > 0 && itemId > 0,
    retry: false,
  })
}

/** Kho khảo sát đã duyệt cho một dòng — giữ trang cũ khi lật trang cho đỡ nháy. */
export function usePrAvailableSurveyLines(
  prId: number,
  itemId: number,
  params: AvailablePrSurveyLinesParams,
  enabled: boolean,
) {
  return useQuery({
    queryKey: queryKeys.procurement.purchaseRequestAvailableSurveyLines(prId, itemId, {
      ...params,
    }),
    queryFn: () => purchaseRequestOptionApi.listAvailableSurveyLines(prId, itemId, params),
    enabled: prId > 0 && itemId > 0 && enabled,
    placeholderData: keepPreviousData,
    retry: false,
  })
}

export function useAttachSurveyOption(prId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      itemId,
      productSurveyLineId,
    }: {
      itemId: number
      productSurveyLineId: number
    }) => purchaseRequestOptionApi.addFromSurvey(prId, itemId, productSurveyLineId),
    onSuccess: () => {
      toast.success('Đã gắn phương án từ khảo sát')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

export function useAddManualOption(prId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ itemId, payload }: { itemId: number; payload: PrOptionManualPayload }) =>
      purchaseRequestOptionApi.addManual(prId, itemId, payload),
    onSuccess: () => {
      toast.success('Đã thêm phương án nhập tay')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

export function useUpdateOption(prId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      itemId,
      optionId,
      payload,
    }: {
      itemId: number
      optionId: number
      payload: PrOptionUpdatePayload
    }) => purchaseRequestOptionApi.update(prId, itemId, optionId, payload),
    onSuccess: () => {
      toast.success('Đã cập nhật phương án')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

export function useRemoveOption(prId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ itemId, optionId }: { itemId: number; optionId: number }) =>
      purchaseRequestOptionApi.remove(prId, itemId, optionId),
    onSuccess: () => {
      toast.success('Đã gỡ phương án')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

/** Chốt / bỏ chốt. `wasChosen` chỉ để chọn câu toast — backend tự đảo trạng thái. */
export function useChooseOption(prId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      itemId,
      optionId,
    }: {
      itemId: number
      optionId: number
      wasChosen: boolean
    }) => purchaseRequestOptionApi.choose(prId, itemId, optionId),
    onSuccess: (_data, variables) => {
      toast.success(variables.wasChosen ? 'Đã bỏ chốt phương án' : 'Đã chốt phương án')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

/** Khe H.10.4 — thu mua điền/sửa NCC (kèm giá) trên phương án 0 / nhập tay, kể cả sau chốt. */
export function useSetPrOptionSupplier(prId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      itemId,
      optionId,
      payload,
    }: {
      itemId: number
      optionId: number
      payload: PrOptionSupplierPayload
    }) => purchaseRequestOptionApi.setSupplier(prId, itemId, optionId, payload),
    onSuccess: () => {
      toast.success('Đã áp nhà cung cấp vào phương án')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

/** H.10.5 — áp MỘT NCC vào phương án đang chọn của nhiều dòng, một lượt trên màn chọn. */
export function useAssignPrSupplierBulk(prId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: PrAssignSupplierPayload) =>
      purchaseRequestOptionApi.assignSupplierBulk(prId, payload),
    onSuccess: (data) => {
      toast.success(`Đã áp nhà cung cấp cho ${data.updated} dòng`)
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

/** Đợt 3b — NSTM chốt hoàn thành xử lý phần của mình (dòng trống phải tick chốt rỗng). */
export function useCompletePrOptions(prId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (emptyItemIds: number[]) =>
      purchaseRequestOptionApi.complete(prId, emptyItemIds),
    onSuccess: (data) => {
      toast.success(
        data.all_done
          ? 'Đã chốt hoàn thành xử lý — cả phiếu đã xử lý xong'
          : 'Đã chốt hoàn thành xử lý phương án',
      )
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

/**
 * H.10.6 — nút "Tạo đơn mua hàng theo phương án": gom dòng đã chọn theo NCC
 * thành N đơn nháp một lượt. Toast kể tên các đơn vừa sinh để người bấm lần
 * theo được ngay; invalidate cả nhánh procurement vì trạng thái dòng YCMH và
 * danh sách ĐMH cùng đổi.
 */
export function useGeneratePrOrders(prId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => purchaseRequestOptionApi.generateOrders(prId),
    onSuccess: (data) => {
      const codes = data.orders.map((o) => o.code).join(', ')
      toast.success(`Đã tạo ${data.orders.length} đơn mua hàng nháp: ${codes}`)
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

/** Đợt 3b — người yêu cầu / quản lý mở lại một dòng đã chốt cho NSTM xử lý tiếp. */
export function useReopenPrOptionsLine(prId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (itemId: number) => purchaseRequestOptionApi.reopenLine(prId, itemId),
    onSuccess: () => {
      toast.success('Đã mở lại dòng cho NSTM xử lý tiếp')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}
