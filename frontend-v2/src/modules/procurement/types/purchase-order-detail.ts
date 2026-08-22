/**
 * Kiểu dữ liệu Đơn mua hàng (ĐMH) bản CHI TIẾT — khớp `_out()` của
 * `backend/app/modules/purchase_order/controller.py`.
 *
 * Khác `PurchaseOrder` trong `purchase-document.ts`: bản kia là dòng DANH SÁCH
 * (ít cột, backend cắt bớt), bản này có đủ dòng hàng + lần giao + số tiền.
 */

/** Một LẦN GIAO của dòng hàng — nhận hàng nhiều đợt thì mỗi đợt một bản ghi. */
export interface PurchaseOrderDelivery {
  id?: number
  delivery_no: number
  warehouse_code: string
  carrier_code: string
  carrier_name: string
  ship_qty: number
  ship_unit: string
  received_qty: number
  promised_date: string
  expected_date: string
  received_date: string
  std_days: number
  /** Ba mốc lệch ngày do backend tính, chỉ đọc. */
  regulated_date?: string
  diff_promise?: number
  diff_regulated?: number
  diff_required?: number
  invoice_no: string
  invoice_date: string
  shipping_unit_price: number
  shipping_amount: number
  qc_result: string
  status?: string
  extra_request: string
  progress_note: string
  /** Công nợ HÀNG của lần giao (backend cộng từ bảng công nợ). Chỉ đọc. */
  goods_total?: number
  paid?: number
  remaining?: number
}

/** Một dòng hàng của ĐMH. */
export interface PurchaseOrderItem {
  /** Thiếu = dòng mới chưa lưu. GIỮ id khi sửa, mất id là backend xóa rồi tạo lại dòng. */
  id?: number
  product_code: string
  product_name: string
  /** Tên ghi trên hóa đơn — lấy từ danh mục sản phẩm, sửa tay được. */
  invoice_name: string
  item_group: string
  spec: string
  /** Mã/tên thành phẩm (hàng hóa) gắn với sản phẩm. */
  fg_code: string
  fg_name: string
  invoice_no: string
  invoice_date: string
  /** Ngày giao chứng từ cho kế toán. */
  document_delivery_date: string
  /** NCC có sẵn hàng — quyết định lấy mốc ngày quy định nào khi tính Đơn gấp. */
  supplier_ready: boolean
  required_date: string
  /**
   * Ngày dự kiến có hàng. Bỏ trống thì backend tự điền: lấy theo dòng YCMH
   * nguồn, không có thì tính từ thời gian chuẩn của phân loại. Tự điền HỤT
   * (dòng thêm tay, phân loại chưa khai thời gian chuẩn) thì ô ở lại rỗng và
   * cổng CR-095 chặn gửi duyệt — nên màn phải có ô để sửa tay.
   */
  expected_date: string
  unit: string
  qty_request: number
  qty_order: number
  price: number
  /** % VAT theo TỪNG DÒNG (header còn `vat_rate` làm mặc định). */
  vat: number
  warehouse_code: string
  note: string

  /** Từ đây trở xuống là số liệu backend tính — không gửi lên khi lưu. */
  amount?: number
  qty_received?: number
  qty_remaining?: number
  line_status?: string
  progress_status?: string
  pause_reason?: string
  status_before_pause?: string
  is_short_delivery?: boolean
  order_total?: number
  goods_total?: number
  paid_total?: number
  remaining_total?: number

  deliveries: PurchaseOrderDelivery[]
}

/** ĐMH bản chi tiết — `GET /api/purchase-orders/{id}`. */
export interface PurchaseOrderDetail {
  id: number
  code: string
  misa_code: string
  /** Mã YCMH nguồn — chuỗi mã, KHÔNG phải id. */
  pr_code: string
  survey_code: string
  company_id: number
  supplier_code: string
  supplier_name: string
  department: string
  /** Nhân sự thu mua phụ trách. */
  nspt: string
  order_date: string
  vat_rate: number
  payment_terms: string
  is_urgent: boolean
  status: string
  /** Tình trạng hồ sơ chứng từ — lưu CHUỖI TIẾNG VIỆT, cập nhật tay. */
  document_status: string
  note: string
  approve_note?: string

  items: PurchaseOrderItem[]

  /** Tiền theo SL THỰC NHẬN (đã chốt). */
  subtotal: number
  vat: number
  total: number
  shipping_total: number
  /** Tiền theo SL ĐẶT (dùng cho bản in gửi NCC). */
  order_subtotal: number
  order_total: number
  /** Công nợ chưa trả (hàng + vận chuyển) — bật nút tạo yêu cầu thanh toán. */
  unpaid_total: number
}

/** Tiến độ của một DÒNG hàng. 4 bước đầu backend tự chuyển theo dữ liệu. */
export const PO_LINE_PROGRESS = [
  'Chưa đặt hàng',
  'Đã đặt hàng',
  'Đã nhận hàng',
  'Chưa gửi ĐMH cho KT',
  'Đã gửi ĐMH cho KT',
  'Hoàn thành',
  'Tạm ngưng',
  'Hủy đơn',
] as const

/** Mức VAT hay dùng cho ô chọn ở dòng hàng. */
export const PO_VAT_OPTIONS = [0, 5, 8, 10] as const

/** Hình thức thanh toán NCC — giữ đúng danh sách của bản v1. */
export const PAYMENT_TERMS_OPTIONS = [
  'Công nợ 60 ngày',
  'Công nợ 30 ngày',
  'Công nợ 20 ngày',
  'Thanh toán 100% khi nhận hàng',
  'Thanh toán trước khi giao hàng',
  'Thanh toán 7 ngày sau khi nhận hàng',
] as const

/** Đơn đã chốt/hủy -> khóa mọi thao tác ghi. */
export function isPurchaseOrderLocked(status: string): boolean {
  return ['completed', 'cancelled'].includes(status)
}

/**
 * Đơn đã được duyệt (CR-108, phiếu hỗ trợ TK19082604).
 *
 * Từ mốc này nội dung đơn là thứ trưởng phòng đã ký, không sửa được nữa — chỉ còn
 * mở vài ô PHÁT SINH SAU KHI DUYỆT (xem `PO_FIELDS_EDITABLE_AFTER_APPROVE`). Muốn
 * đổi phần đã duyệt thì bấm "Hủy duyệt" để đơn về Nháp rồi gửi duyệt lại. Backend
 * chặn y hệt (`chan_sua_don_da_duyet`), đây chỉ là lớp khóa cho êm tay.
 */
export function isPurchaseOrderApproved(status: string): boolean {
  return ['approved', 'partial', 'received'].includes(status)
}

/** Nhãn các ô còn sửa được sau khi duyệt — dùng cho câu nhắc trên màn. */
export const PO_FIELDS_EDITABLE_AFTER_APPROVE =
  'Tên trên hóa đơn · Ngày dự kiến có hàng · Kho nhận mặc định · Ghi chú · Ngày giao chứng từ cho KT · Giao hàng nhiều lần'

/** Đơn đã duyệt trở đi mới nhập được tiến độ giao hàng. */
export function isDeliveryStage(status: string): boolean {
  return ['approved', 'partial', 'received'].includes(status)
}

/** Dòng đã chốt -> khóa hẳn dòng đó. */
export function isLineLocked(item: PurchaseOrderItem): boolean {
  // B-06: cột lưu MÃ, xem PO_PROGRESS_STATUS trong shared/constants/statuses.ts
  return ['completed', 'cancelled'].includes(item.progress_status ?? '')
}

/**
 * Dòng ĐÃ NHẬN HÀNG thì cấm đổi nhận diện sản phẩm (mã hàng, tên, ĐVT): phiếu
 * nhập kho và tồn kho đã ghi theo mã cũ. Backend cũng chặn.
 */
export function isLineReceived(item: PurchaseOrderItem): boolean {
  return (item.qty_received ?? 0) > 0
}

export const PRODUCT_LOCK_HINT =
  'Dòng đã nhận hàng — không đổi được Mã hàng / Tên hàng / ĐVT. Hủy dòng rồi thêm dòng mới nếu cần.'
