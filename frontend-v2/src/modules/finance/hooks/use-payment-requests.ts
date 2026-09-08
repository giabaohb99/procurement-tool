import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'
import { toast } from 'sonner'

import { appConfig } from '@/core/config/app-config'
import { queryKeys } from '@/shared/constants/query-keys'
import type { ListParams } from '@/shared/types/api'
import { paymentRequestApi } from '../api/payment-request-api'
import type {
  PaymentRequestCreateInput,
  PaymentRequestUpdateInput,
} from '../types/payment-request'

/**
 * Danh sách YCTT. `keepPreviousData`: đổi trang / bộ lọc thì giữ bảng cũ thay vì
 * nháy sang khung rỗng.
 *
 * `enabled`: dành cho những trang mượn danh sách này để đếm (bảng Tổng quan) —
 * người không có quyền `payment_request.read` thì đừng gọi, gọi là ăn 403 vô ích.
 */
export function usePaymentRequests(params: ListParams = {}, options: { enabled?: boolean } = {}) {
  const query: ListParams = { page: 1, page_size: appConfig.defaultPageSize, ...params }
  return useQuery({
    queryKey: queryKeys.finance.paymentRequests(query),
    queryFn: () => paymentRequestApi.list(query),
    placeholderData: keepPreviousData,
    enabled: options.enabled ?? true,
  })
}

/** Chi tiết một phiếu — bỏ qua khi chưa có id (màn TẠO). */
export function usePaymentRequest(id: number) {
  return useQuery({
    queryKey: queryKeys.finance.paymentRequest(id),
    queryFn: () => paymentRequestApi.getById(id),
    enabled: id > 0,
  })
}

/** Dữ liệu bản in — khóa riêng vì hình dạng khác chi tiết và cần quyền `print`. */
export function usePaymentRequestPrintData(id: number) {
  return useQuery({
    queryKey: [...queryKeys.finance.paymentRequest(id), 'print'] as const,
    queryFn: () => paymentRequestApi.printData(id),
    enabled: id > 0,
  })
}

/**
 * TẠO phiếu. Trả về MẢNG phiếu (server tách theo NCC × loại nợ) nên phần thông
 * báo + điều hướng để màn tự lo — nó biết đếm mấy phiếu.
 *
 * Lỗi non-GET đã được `httpClient` tự toast, ở đây không toast lại.
 */
export function useCreatePaymentRequests() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: PaymentRequestCreateInput) => paymentRequestApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.finance.all })
    },
  })
}

/** SỬA bản nháp. */
export function useUpdatePaymentRequest(id: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: PaymentRequestUpdateInput) => paymentRequestApi.update(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.finance.all })
      toast.success('Đã lưu yêu cầu thanh toán')
    },
  })
}

/** XÓA bản nháp. Điều hướng về danh sách để màn tự lo sau khi xóa. */
export function useDeletePaymentRequest() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => paymentRequestApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.finance.all })
      toast.success('Đã xóa yêu cầu thanh toán')
    },
  })
}

/** Bốn chuyển trạng thái: gửi duyệt · duyệt · từ chối · ghi nhận đã chi. */
export type PaymentRequestAction = 'submit' | 'approve' | 'reject' | 'pay'

const ACTION_TOAST: Record<PaymentRequestAction, string> = {
  submit: 'Đã gửi duyệt',
  approve: 'Đã duyệt phiếu',
  reject: 'Đã từ chối phiếu',
  pay: 'Đã ghi nhận chi — công nợ được trừ tương ứng',
}

/**
 * Chuyển trạng thái phiếu. Ghi nhận chi (`pay`) tác động cả sang Công nợ nên làm
 * mất hiệu lực toàn nhánh `finance` để bảng công nợ cũng nạp lại.
 */
export function usePaymentRequestAction(id: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ action, reason }: { action: PaymentRequestAction; reason?: string }) => {
      switch (action) {
        case 'submit':
          return paymentRequestApi.submit(id)
        case 'approve':
          return paymentRequestApi.approve(id)
        case 'reject':
          return paymentRequestApi.reject(id, reason ?? '')
        case 'pay':
          return paymentRequestApi.pay(id)
      }
    },
    onSuccess: (_data, { action }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.finance.all })
      toast.success(ACTION_TOAST[action])
    },
  })
}

/**
 * CR-268 — tiền treo của một NCC (phiếu trả trước đã chi, chưa đối trừ/hoàn hết).
 * `po_code` -> treo gắn đúng đơn đó · `unlinked: 1` -> chỉ treo cấp NCC (không gắn đơn).
 * `enabled`: chỉ gọi khi thật sự cần (có NCC + có quyền `payment_request.read`).
 */
export function usePrepayHanging(
  params: { supplier_code: string; po_code?: string; unlinked?: number; source_type?: string },
  options: { enabled?: boolean } = {},
) {
  return useQuery({
    queryKey: queryKeys.finance.prepayHanging(params),
    queryFn: () => paymentRequestApi.hanging(params),
    enabled: (options.enabled ?? true) && Boolean(params.supplier_code),
  })
}

/**
 * CR-268 — ghi nhận NCC hoàn tiền phần treo của phiếu trả trước đã chi.
 * Đổi số trên cả phiếu lẫn tiền treo -> làm mất hiệu lực toàn nhánh `finance`.
 */
export function useRefundPrepay(id: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: { amount: number; note: string }) =>
      paymentRequestApi.refund(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.finance.all })
      toast.success('Đã ghi nhận nhà cung cấp hoàn tiền')
    },
  })
}
