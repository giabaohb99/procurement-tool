/**
 * Công nợ phải trả — khớp `_out()` của `backend/app/modules/payable/controller.py`.
 *
 * Bảng `tab_payable` KHÔNG do người dùng nhập: mỗi lần nhận hàng backend sinh
 * ngầm một dòng (`service.upsert`), nên màn này chỉ đọc. Một dòng = một lần giao
 * × một luồng (hàng hóa / vận chuyển).
 */
export interface Payable {
  id: number
  company_id: number
  /** Mã NCC — khóa DUY NHẤT toàn hệ, đây mới là thứ để lọc/nối bảng. */
  supplier_code: string
  /**
   * BẢN CHỤP tên NCC lúc phát sinh nợ. Cố ý chụp lại: khoản nợ là chứng từ tài
   * chính, NCC đổi tên sau này thì sổ nợ cũ vẫn phải đọc ra tên lúc ký nhận.
   */
  supplier_name: string
  source_type: PayableSourceType
  po_id: number
  po_code: string
  /** Rỗng = chưa có hóa đơn -> chưa lên được yêu cầu thanh toán. */
  invoice_no: string
  /** Ngày phát sinh (= ngày nhận hàng), dạng `YYYY-MM-DD`. */
  incur_date: string
  /** Hạn trả, suy từ hình thức thanh toán của NCC. */
  due_date: string
  created_at: string
  /** Tiền trước VAT. */
  amount: number
  vat: number
  /** Phải trả = amount + vat. */
  total: number
  paid_amount: number
  /** Tính sẵn ở backend = total - paid_amount, KHÔNG cộng lại ở đây. */
  remaining: number
  status: string
  /** Nhóm tuổi nợ, backend tính theo `due_date` so với hôm nay. */
  aging: string
}

/** Bốn số tổng của `/api/payables/summary`, lấy theo ĐÚNG bộ lọc đang áp. */
export interface PayableSummary {
  total: number
  paid: number
  remaining: number
  overdue: number
}

/** `goods` = nợ NCC bán hàng · `shipping` = nợ đơn vị vận chuyển. */
export type PayableSourceType = 'goods' | 'shipping'

export const PAYABLE_SOURCE_LABELS: Record<string, string> = {
  goods: 'Hàng hóa',
  shipping: 'Vận chuyển',
}

/**
 * DB lưu chuỗi VIẾT TẮT tiếng Việt (không phải mã enum). Giá trị gửi lên khi lọc
 * phải là chuỗi gốc bên trái, chỉ phần hiện ra mới dùng nhãn đầy đủ.
 */
export const PAYABLE_STATUS_LABELS: Record<string, string> = {
  'Chờ TT': 'Chờ thanh toán',
  'Trả một phần': 'Thanh toán một phần',
  'Đã TT': 'Đã thanh toán',
}

/** Thứ tự đúng bằng thứ tự backend phân nhóm trong `service.aging_bucket`. */
export const AGING_BUCKETS = ['Chưa đến hạn', '1-30', '31-60', '61-90', '>90'] as const

/**
 * Nhãn nhóm tuổi nợ. Backend trả về khoảng ngày trần (`1-30`, `>90`) — thiếu chữ
 * "ngày" thì đọc trên bảng không biết đó là ngày, tiền hay số phiếu.
 */
export function agingLabel(bucket: string): string {
  if (!bucket) return ''
  return bucket === 'Chưa đến hạn' ? bucket : `${bucket} ngày`
}

/** Đổi bảng nhãn thành mảng option cho ô chọn, giữ nguyên thứ tự khai báo. */
export function payableStatusOptions(): { value: string; label: string }[] {
  return Object.entries(PAYABLE_STATUS_LABELS).map(([value, label]) => ({ value, label }))
}
