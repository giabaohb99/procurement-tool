import { apiDelete, apiGet, apiPatch, apiPost } from '@/core/api'
import type { ListParams, PaginatedResult } from '@/shared/types/api'
import type {
  HangingSummary,
  PaymentRequest,
  PaymentRequestCreateInput,
  PaymentRequestPrint,
  PaymentRequestSummary,
  PaymentRequestUpdateInput,
} from '../types/payment-request'

const BASE_URL = '/api/payment-requests'

/**
 * Yêu cầu thanh toán (YCTT).
 *
 * ⚠️ `create` trả về MẢNG phiếu: backend tách mỗi (NCC × loại công nợ) thành một
 * phiếu riêng, nên một payload có thể sinh nhiều phiếu.
 *
 * Whitelist lọc của list (`service.FILTERABLE`): code · supplier_code · status ·
 * source_type · request_date · payment_method. Controller tự đọc thêm
 * `company_id` (bằng) và `po_code` (dò qua bảng dòng).
 */
export const paymentRequestApi = {
  list: (params: ListParams) =>
    apiGet<PaginatedResult<PaymentRequestSummary>>(BASE_URL, { params }),

  getById: (id: number) => apiGet<PaymentRequest>(`${BASE_URL}/${id}`),

  /** Dữ liệu đầy đủ cho bản in (cần quyền `payment_request.print`). */
  printData: (id: number) => apiGet<PaymentRequestPrint>(`${BASE_URL}/${id}/print`),

  create: (payload: PaymentRequestCreateInput) => apiPost<PaymentRequest[]>(BASE_URL, payload),

  update: (id: number, payload: PaymentRequestUpdateInput) =>
    apiPatch<PaymentRequest>(`${BASE_URL}/${id}`, payload),

  remove: (id: number) => apiDelete<null>(`${BASE_URL}/${id}`),

  submit: (id: number) => apiPost<PaymentRequest>(`${BASE_URL}/${id}/submit`),

  approve: (id: number) => apiPost<PaymentRequest>(`${BASE_URL}/${id}/approve`),

  reject: (id: number, reason: string) =>
    apiPost<PaymentRequest>(`${BASE_URL}/${id}/reject`, { reason }),

  pay: (id: number) => apiPost<PaymentRequest>(`${BASE_URL}/${id}/pay`),

  /**
   * CR-268 — tiền treo (phiếu trả trước đã chi, chưa đối trừ hết) của một NCC.
   * `po_code` -> chỉ treo gắn đúng đơn đó · `unlinked: 1` -> chỉ treo cấp NCC.
   */
  hanging: (params: { supplier_code: string; po_code?: string; unlinked?: number; source_type?: string }) =>
    apiGet<HangingSummary>(`${BASE_URL}/hanging`, { params }),

  /** CR-268 — ghi nhận NCC hoàn tiền phần treo. `amount` 0/bỏ trống = hoàn toàn bộ. */
  refund: (id: number, payload: { amount: number; note: string }) =>
    apiPost<PaymentRequest>(`${BASE_URL}/${id}/refund`, payload),
}
