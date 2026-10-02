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
  /** bao-CR-304 (ticket 26) — mã MISA của ĐMH khớp theo mã PO, chỉ hiển thị (nhập/sửa trên ĐMH). */
  misa_code: string
  invoice_no: string
  invoice_date: string
  amount: number
  due_date: string
  incur_date: string
  payable_total: number
  payable_paid: number
  /** Đã khớp được vào một khoản công nợ hay chưa. */
  matched: boolean
  /** CR-268 — chỉ có nghĩa với phiếu `prepay=1` đã chi: phần đã ĐỐI TRỪ vào công nợ. */
  allocated_amount: number
  /** CR-268 — phần NCC đã HOÀN TIỀN lại (ghi nhận tay). */
  refunded_amount: number
  /**
   * CR-260 — phần đề nghị CẤN TRỪ tiền treo cấp NCC vào khoản nợ của dòng.
   * Lúc phiếu còn nháp/chờ duyệt chỉ là Ý ĐỊNH; backend THỰC THI khi bấm Duyệt.
   */
  offset_amount: number
  /** CR-268 — tiền TREO còn lại = amount - allocated_amount - refunded_amount. */
  hanging: number
  /**
   * bao-CR-509 — nợ còn lại HIỆN TẠI của các khoản khớp dòng và số đề nghị ĐÁNG RA theo
   * công nợ. `null` = dòng không theo dõi (phiếu đã chi / đã từ chối / trả trước).
   * Luật tính nằm ở `service.plan_refresh` của backend — đừng tự tính lại ở đây.
   */
  payable_remaining?: number | null
  expected_amount?: number | null
  /** bao-CR-509 — số trên dòng đang lệch công nợ hiện tại. */
  out_of_sync?: boolean
}

/** bao-CR-509 — tình trạng một dòng khi so với công nợ hiện tại (mã do backend trả). */
export type PaymentRefreshState =
  | 'changed'
  | 'unchanged'
  | 'manual'
  | 'payable_missing'
  | 'paid_off'
  | 'duplicate'

/** bao-CR-509 — một dòng của bản xem trước «Cập nhật theo công nợ»: số cũ → số mới. */
export interface PaymentRefreshLine {
  line_id: number
  index: number
  state: PaymentRefreshState
  /** Câu giải thích do backend dựng (nợ còn lại, cấn trừ, tất toán…). */
  reason: string
  payable_ids: number[]
  payable_remaining: number | null
  offset_amount: number
  po_code_old: string
  po_code_new: string
  invoice_no_old: string
  invoice_no_new: string
  invoice_date_old: string
  invoice_date_new: string
  amount_old: number
  amount_new: number
  amount_changed: boolean
  changed: boolean
}

/** bao-CR-509 — kết quả `GET /api/payment-requests/{id}/refresh-preview` (không ghi gì). */
export interface PaymentRefreshPlan {
  request_id: number
  code: string
  status: PaymentRequestStatus
  prepay: number
  /** Chỉ phiếu Nháp, không phải trả trước, mới ghi được. */
  can_apply: boolean
  blocked_reason: string
  old_total: number
  new_total: number
  changed_count: number
  out_of_sync: boolean
  lines: PaymentRefreshLine[]
}

/**
 * CR-268 — một dòng tiền treo trả về từ `GET /api/payment-requests/hanging`:
 * phiếu trả trước ĐÃ CHI còn phần chưa đối trừ / chưa được hoàn.
 */
export interface HangingItem {
  request_id: number
  request_code: string
  request_date: string
  line_id: number
  /** Rỗng = treo CẤP NCC (không gắn đơn nào). */
  po_code: string
  amount: number
  allocated_amount: number
  refunded_amount: number
  hanging: number
}

/** CR-268 — gói tổng tiền treo của một NCC (lọc được theo đơn / chỉ cấp NCC). */
export interface HangingSummary {
  total: number
  items: HangingItem[]
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
  /** bao-CR-304 (ticket 26) — mã MISA các dòng gộp thành "MS1, MS2" (phiếu gồm nhiều PO). */
  misa_code: string
  created_by_name: string
  /** Lần sửa gần nhất — cột "Ngày cập nhật" (bao-CR-300, ticket 21). */
  updated_at?: string
  /**
   * bao-CR-553 — «Trưởng bộ phận» in ở dòng «Trưởng phòng ban/bộ phận» của bản in (id NHÂN SỰ + tên
   * đã chép). 0 / rỗng = mặc định trưởng phòng của người lập.
   */
  head_of_dept_id?: number
  head_of_dept?: string
}

/** bao-CR-553 — một người trong ô «Trưởng bộ phận» (cùng dạng với YCMH/YCBG/ĐMH). */
export interface PaymentApprovalCandidate {
  employee_id: number
  code: string
  name: string
  position: string
}

/**
 * CR-149 (main, ticket #14): 3 câu chữ bản in người dùng sửa được.
 * Khóa nào vắng -> bản in in câu tự động theo `prepay` (CR-146) như cũ.
 */
export interface PrintTexts {
  /** Dòng "Nội dung" trong khối NỘI DUNG THANH TOÁN. */
  content?: string
  /** Cột "Diễn giải" của bảng Đề nghị thanh toán. */
  line_desc?: string
  /** Dòng "Nội dung chuyển khoản" (tiền mặt vẫn để trống theo CR-035). */
  transfer?: string
}

/** Chi tiết một phiếu — thêm ngày tạo và danh sách dòng. */
export interface PaymentRequest extends PaymentRequestSummary {
  created_at: string
  lines: PaymentRequestLine[]
  /** CR-149: `_out()` trả dict đã parse (rỗng = chưa sửa, in câu tự động). */
  print_texts: PrintTexts
  /**
   * bao-CR-509 — số đề nghị trên phiếu đang lệch công nợ hiện tại (chỉ tính cho phiếu
   * Nháp / Chờ duyệt / Đã duyệt, không phải trả trước).
   */
  out_of_sync?: boolean
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
  /** CR-260 — phần cấn trừ tiền treo đề nghị trên dòng (thực thi khi Duyệt). */
  offset_amount?: number
}

/**
 * Payload TẠO — server tách theo (supplier_code × source_type), trả về MẢNG phiếu.
 *
 * CR-149 từng BỎ ô chọn `prepay` (lúc đó cờ chỉ đổi câu chữ bản in). CR-268 cho cờ
 * này nghĩa THẬT — phiếu trả trước được duyệt-chi không cần khớp công nợ, tiền chi
 * thành TIỀN TREO chờ đối trừ — nên ô chọn quay lại ở chế độ form trắng.
 */
export interface PaymentRequestCreateInput {
  request_date: string
  note: string
  payment_method: PaymentMethod
  /** CR-268: `1` = phiếu THANH TOÁN TRƯỚC / tạm ứng NCC (miễn cổng khớp công nợ CR-066). */
  prepay?: number
  supplier_code: string
  company_id: number
  source_type: string
  lines: PaymentRequestLineInput[]
  /** bao-CR-553 — ô Trưởng bộ phận; mặc định 0 / "" = như trước. */
  head_of_dept_id?: number
  head_of_dept?: string
}

/**
 * Payload SỬA — các ô đầu phiếu cho sửa được và danh sách dòng (chỉ bản nháp).
 * CR-149: payload CHỈ chứa `print_texts` thì backend cho sửa cả khi phiếu đã
 * gửi duyệt / đã duyệt (người dùng in phiếu sau khi duyệt).
 */
export interface PaymentRequestUpdateInput {
  request_date?: string
  note?: string
  payment_method?: PaymentMethod
  lines?: PaymentRequestLineInput[]
  print_texts?: PrintTexts
  /** bao-CR-553 — chỉ nhận khi phiếu Nháp. */
  head_of_dept_id?: number
  head_of_dept?: string
}

/** Đổi bảng nhãn trạng thái thành mảng option cho ô chọn, giữ nguyên thứ tự khai báo. */
export function paymentRequestStatusOptions(): { value: string; label: string }[] {
  return Object.entries(PAYMENT_REQUEST_STATUS_LABELS).map(([value, label]) => ({ value, label }))
}
