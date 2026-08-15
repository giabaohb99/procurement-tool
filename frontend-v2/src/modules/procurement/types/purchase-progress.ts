/**
 * Tiến độ mua hàng — `/api/purchase-progress`.
 *
 * KHÔNG phải một bảng trong DB mà là báo cáo phẳng theo TỪNG LẦN GIAO của từng
 * dòng đơn mua hàng: một ĐMH có 3 dòng, mỗi dòng giao 2 lần -> 6 dòng ở đây.
 */
export interface PurchaseProgressRow {
  /** Số thứ tự do backend đánh sẵn (có thể thiếu -> trang tự tính). */
  stt?: number
  po_id: number
  po_code: string
  misa_code: string
  pr_code: string
  company_id: number
  department: string
  supplier_code: string
  supplier_name: string
  nspt: string
  order_date: string
  product_code: string
  product_name: string
  item_group: string
  spec: string
  invoice_no: string
  required_date: string
  unit: string
  qty_request: number
  qty_order: number
  price: number
  vat: number
  order_amount: number
  /** Tiến độ dòng — chuỗi tiếng Việt, xem `PROGRESS_STATUSES`. */
  progress_status: string
  /** Lần giao thứ mấy. */
  delivery_no: number | null
  warehouse_code: string
  carrier_code: string
  carrier_name: string
  ship_qty: number
  received_qty: number
  promised_date: string
  expected_date: string
  received_date: string
  std_days: number
  regulated_date: string
  /** Chênh lệch ngày: âm = trễ, dương = sớm. */
  diff_promise: number
  diff_regulated: number
  diff_required: number
  shipping_unit_price: number
  shipping_amount: number
  qc_result: string
  delivery_status: string
  /** Thành tiền theo số đã nhận. */
  amount: number
  document_status: string
}

export interface PurchaseProgressResult {
  total: number
  items: PurchaseProgressRow[]
  /**
   * Người dùng có quyền `supplier.read` không. Không có thì backend đã xóa
   * trắng cột NCC / vận chuyển — màn hình ẩn luôn mấy cột đó cho đỡ rối.
   */
  show_supplier: boolean
}

/** Tiến độ của một dòng đơn hàng. Thứ tự dưới đây là thứ tự trong luồng. */
export const PROGRESS_STATUSES = [
  'Chưa đặt hàng',
  'Đã đặt hàng',
  'Đã nhận hàng',
  'Chưa gửi ĐMH cho KT',
  'Đã gửi ĐMH cho KT',
  'Hoàn thành',
  'Tạm ngưng',
  'Hủy đơn',
] as const
