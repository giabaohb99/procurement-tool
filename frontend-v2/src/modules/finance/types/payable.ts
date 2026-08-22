import { PAYABLE_STATUS, labelOf } from '@/shared/constants/statuses'

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
  /**
   * MÃ tiếng Anh (B-05): `unpaid` | `partial` | `paid`.
   *
   * KHÔNG do người dùng chọn — backend tính lại từ `paid_amount` so với `total` sau mỗi
   * lần phân bổ thanh toán, nên nó có thể LÙI (`paid` -> `partial`) khi hóa đơn đổi số.
   * Đừng coi `paid` là trạng thái kết.
   */
  status: string
  /** Nhãn tiếng Việt của `status`, backend gửi kèm. Rỗng khi mã lạ. */
  status_label: string
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
 * Trạng thái công nợ — sinh từ `backend/app/core/status_codes.py`, KHÔNG khai lại ở đây.
 *
 * Trước B-05 chỗ này là một bảng dịch tay `'Chờ TT' -> 'Chờ thanh toán'`: DB lưu chữ viết
 * tắt, màn hình hiện chữ đầy đủ. Nay DB lưu MÃ (`unpaid | partial | paid`) và nhãn đầy đủ
 * nằm trong bộ mã dùng chung, nên không còn hai bảng chữ phải giữ cho khớp nữa.
 *
 * Giá trị gửi lên khi LỌC phải là `value` (mã), không phải nhãn.
 */
export const PAYABLE_STATUS_OPTIONS = PAYABLE_STATUS.map(({ value, label }) => ({
  value,
  label,
}))

/** Nhãn của một mã trạng thái. Mã lạ thì trả NGUYÊN mã, không trả rỗng. */
export function payableStatusLabel(value?: string | null): string {
  const v = (value ?? '').trim()
  if (!v) return ''
  return labelOf(PAYABLE_STATUS, v) || v
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
