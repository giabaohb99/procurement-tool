import { apiGet, apiPost } from '@/core/api'
import type { PaginatedResult } from '@/shared/types/api'

/**
 * Công nợ + Yêu cầu thanh toán (YCTT) nhìn từ màn Đơn mua hàng.
 *
 * Hai API này thuộc phân hệ TÀI CHÍNH; đặt tạm ở đây vì v2 chưa dựng màn YCTT
 * và chỗ dùng duy nhất là nút "Tạo yêu cầu thanh toán" trên ĐMH. Khi có màn
 * YCTT riêng thì chuyển sang `modules/finance/api`.
 */

/** Một khoản công nợ của đơn — mỗi lần nhận hàng / mỗi cước vận chuyển là một dòng. */
export interface Payable {
  id: number
  supplier_code: string
  supplier_name: string
  /** `goods` = tiền hàng (NCC sản xuất), `shipping` = cước vận chuyển. */
  source_type: 'goods' | 'shipping'
  po_code: string
  invoice_no: string
  incur_date: string
  due_date: string
  total: number
  paid_amount: number
  remaining: number
  status: string
}

export interface PaymentRequestLine {
  payable_id: number
  amount: number
}

export const purchaseOrderPaymentApi = {
  /**
   * Công nợ của một đơn. `year: 'all'` vì khoản nợ có thể phát sinh từ năm
   * trước — mặc định backend chỉ trả năm hiện tại.
   */
  listPayables: (poCode: string) =>
    apiGet<PaginatedResult<Payable>>('/api/payables', {
      params: { po_code: poCode, year: 'all', page: 1, page_size: 500 },
    }),

  /**
   * Tạo YCTT. Backend TỰ TÁCH mỗi nhà cung cấp thành một phiếu riêng nên kết
   * quả là một MẢNG phiếu, không phải một phiếu.
   */
  createPaymentRequest: (payload: {
    request_date: string
    note: string
    payment_method: string
    lines: PaymentRequestLine[]
  }) => apiPost<{ id: number; code: string }[]>('/api/payment-requests', payload),
}
