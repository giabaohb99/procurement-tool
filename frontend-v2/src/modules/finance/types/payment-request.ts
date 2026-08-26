/**
 * Yêu cầu thanh toán (YCTT) — khớp `_out()` / `_line()` của
 * `backend/app/modules/payment_request/controller.py`.
 *
 * Một phiếu = một (NCC × loại công nợ). Server tự tách khi tạo: chọn nhiều NCC
 * hoặc cả hàng hóa lẫn vận chuyển thì một lần bấm "Tạo" sinh ra nhiều phiếu.
 */

/** `goods` = nợ NCC bán hàng · `shipping` = nợ đơn vị vận chuyển (dùng lại của Công nợ). */
export type { PayableSourceType as PaymentSourceType } from './payable'
export { PAYABLE_SOURCE_LABELS as PAYMENT_SOURCE_LABELS } from './payable'

/** Chuyển khoản hay tiền mặt — quyết định bản in có in cụm "Thông tin chuyển khoản" (CR-035). */
export type PaymentMethod = 'transfer' | 'cash'

export const PAYMENT_METHOD_LABELS: Record<PaymentMethod, string> = {
  transfer: 'Chuyển khoản',
  cash: 'Tiền mặt',
}

/**
 * Máy trạng thái phẳng: draft → submitted → approved → paid; `cancelled` = bị
 * từ chối (khóa cứng, kèm `reject_reason`).
 */
export type PaymentRequestStatus = 'draft' | 'submitted' | 'approved' | 'paid' | 'cancelled'

export const PAYMENT_REQUEST_STATUS_LABELS: Record<PaymentRequestStatus, string> = {
  draft: 'Nháp',
  submitted: 'Chờ duyệt',
  approved: 'Đã duyệt',
  paid: 'Đã chi',
  cancelled: 'Đã từ chối',
}

/**
 * Một dòng khoản nợ trên phiếu — khớp `_line()`.
 *
 * `due_date` / `payable_total` / `payable_paid` đọc từ CÔNG NỢ (backend tính lúc
 * trả ra), KHÔNG lưu trên phiếu nên không sửa được ở màn này.
 */
export interface PaymentRequestLine {
  id?: number
  /** `0` = dòng gõ tay, chưa gắn khoản nợ nào. */
  payable_id: number
  po_code: string
  invoice_no: string
  invoice_date: string
  amount: number
  due_date: string
  incur_date: string
  payable_total: number
  payable_paid: number
  /** Đã khớp được vào một khoản công nợ hay chưa. */
  matched: boolean
}

/** Phần đầu phiếu — cũng chính là dòng của danh sách (list KHÔNG trả `lines`). */
export interface PaymentRequestSummary {
  id: number
  code: string
  supplier_code: string
  supplier_name: string
  company_id: number
  source_type: string
  request_date: string
  payment_method: PaymentMethod
  /** CR-146 main (ticket #12): 0 = thanh toán công nợ (mặc định) · 1 = thanh toán trước. */
  prepay: number
  total: number
  note: string
  reject_reason: string
  status: PaymentRequestStatus
  created_by_name: string
}

/** Chi tiết một phiếu — thêm ngày tạo và danh sách dòng. */
export interface PaymentRequest extends PaymentRequestSummary {
  created_at: string
  lines: PaymentRequestLine[]
}

/** Dữ liệu bản in `/print` — kèm thông tin đơn vị, người lập và tài khoản nhận. */
export interface PaymentRequestPrint extends PaymentRequest {
  company: { name?: string; address?: string; tax_code?: string }
  created_by_position: string
  created_by_dept: string
  dept_manager: string
  /** Chỉ có khi chuyển khoản. */
  bank_account: string
  bank_name: string
  /** Kỳ công nợ, dạng `YYYY-MM`. */
  period: string
}

/** Một dòng trong payload TẠO / SỬA — chỉ gửi các ô người dùng nhập được. */
export interface PaymentRequestLineInput {
  payable_id: number
  po_code: string
  invoice_no: string
  invoice_date: string
  amount: number
}

/** Payload TẠO — server tách theo (supplier_code × source_type), trả về MẢNG phiếu. */
export interface PaymentRequestCreateInput {
  request_date: string
  note: string
  payment_method: PaymentMethod
  /** CR-146 main: 0 = công nợ (mặc định) · 1 = thanh toán trước. */
  prepay?: number
  supplier_code: string
  company_id: number
  source_type: string
  lines: PaymentRequestLineInput[]
}

/** Payload SỬA bản nháp — chỉ các ô đầu phiếu cho sửa được và danh sách dòng. */
export interface PaymentRequestUpdateInput {
  request_date?: string
  note?: string
  payment_method?: PaymentMethod
  /** CR-146 main: chỉ gửi khi người dùng đổi — 0/1. */
  prepay?: number
  lines?: PaymentRequestLineInput[]
}

/** Đổi bảng nhãn trạng thái thành mảng option cho ô chọn, giữ nguyên thứ tự khai báo. */
export function paymentRequestStatusOptions(): { value: string; label: string }[] {
  return Object.entries(PAYMENT_REQUEST_STATUS_LABELS).map(([value, label]) => ({ value, label }))
}
