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
  /**
   * bao-CR-319 — đồng tiền của DÒNG. Rỗng = theo đơn. `price` / `amount` / `order_total`
   * là NGUYÊN TỆ theo đồng tiền này; `base_amount` là bản QUY ĐỔI về VNĐ (backend tính).
   */
  currency: string
  /** Tỷ giá của dòng; 0 = theo đơn. */
  exchange_rate: number
  /** Khối lượng (kg) — cơ sở chia chi phí lô hàng "theo khối lượng". */
  weight_kg: number
  /** Quy cách / kích thước, chữ tự do. */
  dimension: string

  /** Từ đây trở xuống là số liệu backend tính — không gửi lên khi lưu. */
  amount?: number
  base_amount?: number
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
  /**
   * bao-CR-321 — điều khoản in trên Đơn đặt hàng, chép từ NCC lúc chọn NCC và sửa
   * được theo từng đơn. 0 / rỗng = chưa khai, bản in lùi về NCC rồi về mặc định.
   */
  inspection_days: number
  return_days: number
  invoice_deadline: string
  /** bao-CR-319 — loại đơn: 1 trong nước, 2 nhập khẩu (`ORDER_TYPE_*`). */
  order_type: number
  order_type_label?: string
  /** Đồng tiền + tỷ giá của ĐƠN; dòng để trống thì theo đây. */
  currency: string
  exchange_rate: number
  customs_decl_no: string
  customs_decl_date: string
  is_urgent: boolean
  status: string
  /** Tình trạng hồ sơ chứng từ — lưu CHUỖI TIẾNG VIỆT, cập nhật tay. */
  document_status: string
  note: string
  approve_note?: string

  items: PurchaseOrderItem[]
  /** bao-CR-319 P3 — chi phí lô hàng nhập khẩu; đơn trong nước là mảng rỗng. */
  import_costs: PurchaseOrderImportCost[]
  /** Backend gom sẵn theo loại / theo NCC (P5 tạo YCTT từ đúng số này). */
  import_cost_summary?: ImportCostSummary
  /** Chi phí chia về từng dòng hàng — CHỈ XEM, không lưu, không vào kho. */
  import_cost_allocation?: ImportCostAllocation

  /** Tiền theo SL THỰC NHẬN (đã chốt). */
  subtotal: number
  vat: number
  total: number
  shipping_total: number
  /** Tiền theo SL ĐẶT (dùng cho bản in gửi NCC). */
  order_subtotal: number
  order_total: number
  /** Công nợ chưa trả (hàng + vận chuyển + chi phí lô hàng) — bật nút tạo yêu cầu thanh toán. */
  unpaid_total: number
}

/** Một khoản chi phí của lô hàng nhập khẩu (bao-CR-319 P3). */
export interface PurchaseOrderImportCost {
  /** Thiếu / 0 = dòng mới chưa lưu. */
  id?: number
  /** `IMPORT_COST_TYPE_OPTIONS`. */
  cost_type: number
  cost_type_label?: string
  description: string
  /** NCC nhận tiền của KHOẢN này (hãng tàu, khai thuê, ngân sách nhà nước...). */
  supplier_code: string
  supplier_name: string
  currency: string
  exchange_rate: number
  /** NGUYÊN TỆ, chưa gồm VAT. */
  amount: number
  vat: number
  /** Đã gồm VAT và đã quy đổi VNĐ — backend tính. */
  base_amount?: number
  /** `ALLOCATION_METHOD_OPTIONS`. */
  allocation_method: number
  allocation_method_label?: string
  /** Mã hàng — chỉ dùng khi chia "chỉ định một mã hàng". */
  allocation_target: string
  /** Chia "nhập tay": khóa = id dòng hàng, giá trị = số tiền VNĐ. */
  manual_allocation: Record<string, number>
  invoice_no: string
  invoice_date: string
  payment_due_date: string
  note: string
  /** Công nợ của khoản — backend tính, 0 = chưa thành công nợ. */
  payable_id?: number
  paid_amount?: number
  remaining?: number
  payable_status?: string
}

export interface ImportCostSummaryByType {
  cost_type: number
  cost_type_label: string
  base_amount: number
  count: number
}

export interface ImportCostSummaryBySupplier {
  supplier_code: string
  supplier_name: string
  base_amount: number
  paid_amount: number
  remaining: number
  count: number
  /** Id khoản nợ CÒN NỢ của NCC này — đưa sang màn lập Yêu cầu thanh toán. */
  unpaid_payable_ids: number[]
}

export interface ImportCostSummary {
  goods_base_total: number
  cost_total: number
  paid_total: number
  remaining_total: number
  landed_total: number
  by_type: ImportCostSummaryByType[]
  by_supplier: ImportCostSummaryBySupplier[]
}

export interface ImportCostAllocationShare {
  cost_id: number
  cost_type_label: string
  description: string
  supplier_code: string
  supplier_name: string
  allocation_method: number
  allocation_method_label: string
  /** Cách chia THỰC TẾ áp dụng — khác `allocation_method` khi thiếu cơ sở (0 = chia đều). */
  effective_method: number
  effective_method_label: string
  ratio: number
  base_amount: number
}

export interface ImportCostAllocationLine {
  item_id: number
  product_code: string
  product_name: string
  unit: string
  qty_order: number
  weight_kg: number
  goods_base: number
  cost_base: number
  landed_base: number
  costs: ImportCostAllocationShare[]
}

export interface ImportCostAllocation {
  lines: ImportCostAllocationLine[]
  goods_base_total: number
  cost_total: number
  landed_total: number
  warnings: string[]
}

/** bao-CR-319 — loại đơn mua hàng (SMALLINT ở backend, `OrderType`). */
export const ORDER_TYPE_DOMESTIC = 1
export const ORDER_TYPE_IMPORT = 2
export const ORDER_TYPE_OPTIONS: { value: number; label: string }[] = [
  { value: ORDER_TYPE_DOMESTIC, label: 'Trong nước' },
  { value: ORDER_TYPE_IMPORT, label: 'Nhập khẩu' },
]

export function isImportOrder(order: Pick<PurchaseOrderDetail, 'order_type'>): boolean {
  return Number(order.order_type) === ORDER_TYPE_IMPORT
}

export const DEFAULT_CURRENCY = 'VND'
/** Đồng tiền cho phép chọn; đồng tiền lạ đã lưu vẫn hiện thêm ở ô chọn. */
export const CURRENCY_OPTIONS = ['VND', 'USD', 'CNY', 'EUR', 'JPY', 'KRW', 'THB']

/** Loại chi phí lô hàng — khớp `ImportCostType` + `IMPORT_COST_TYPE_LABELS` backend. */
export const IMPORT_COST_TYPE_OPTIONS: { value: number; label: string }[] = [
  { value: 1, label: 'Cước vận tải quốc tế' },
  { value: 2, label: 'Phí địa phương tại cảng' },
  { value: 3, label: 'Phí dịch vụ hải quan' },
  { value: 4, label: 'Thuế nhập khẩu' },
  { value: 5, label: 'Thuế GTGT hàng nhập khẩu' },
  { value: 6, label: 'Thuế tiêu thụ đặc biệt' },
  { value: 7, label: 'Thuế bảo vệ môi trường' },
  { value: 8, label: 'Phí kiểm tra chuyên ngành' },
  { value: 9, label: 'Bảo hiểm hàng hóa' },
  { value: 10, label: 'Vận chuyển nội địa' },
  { value: 11, label: 'Lưu kho / lưu bãi' },
  { value: 99, label: 'Chi phí khác' },
]
/** Khoản nộp nhà nước — chọn loại này thì ô NCC tự điền "Ngân sách nhà nước". */
export const IMPORT_COST_TAX_TYPES = [4, 5, 6, 7]
export const STATE_BUDGET_SUPPLIER_CODE = 'NSNN'
export const STATE_BUDGET_SUPPLIER_NAME = 'Ngân sách nhà nước'

export function importCostTypeLabel(code: number): string {
  return IMPORT_COST_TYPE_OPTIONS.find((o) => o.value === Number(code))?.label ?? 'Chi phí khác'
}

/** Cách chia chi phí về dòng hàng — khớp `AllocationMethod` backend. */
export const ALLOCATION_BY_VALUE = 1
export const ALLOCATION_BY_WEIGHT = 2
export const ALLOCATION_BY_QUANTITY = 3
export const ALLOCATION_BY_PRODUCT = 4
export const ALLOCATION_MANUAL = 5
export const ALLOCATION_METHOD_OPTIONS: { value: number; label: string }[] = [
  { value: ALLOCATION_BY_VALUE, label: 'Theo giá trị' },
  { value: ALLOCATION_BY_WEIGHT, label: 'Theo khối lượng' },
  { value: ALLOCATION_BY_QUANTITY, label: 'Theo số lượng' },
  { value: ALLOCATION_BY_PRODUCT, label: 'Chỉ định một mã hàng' },
  { value: ALLOCATION_MANUAL, label: 'Nhập tay' },
]
/** Chia nhập tay: tổng các dòng được lệch khoản tối đa chừng này (VNĐ) — khớp backend. */
export const MANUAL_ALLOCATION_TOLERANCE = 1

/** Trạng thái đơn mà chi phí lô hàng đã thành công nợ (chi được) — khớp `IMPORT_COST_PAYABLE_STATUSES`. */
export const PO_IMPORT_COST_PAYABLE_STATUSES = ['approved', 'partial', 'received', 'completed']

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
 * chặn y hệt (`block_edit_approved_order`), đây chỉ là lớp khóa cho êm tay.
 */
export function isPurchaseOrderApproved(status: string): boolean {
  return ['approved', 'partial', 'received'].includes(status)
}

/**
 * Nhãn các ô còn sửa được sau khi duyệt — dùng cho câu nhắc trên màn.
 *
 * Chỉ liệt kê ô nằm TRONG popup chi tiết dòng (nút bút chì ở cột Hành động), vì cả
 * hai câu nhắc đều chỉ người dùng bấm vào đó. Ô ở khối Thông tin chung phải nhắc
 * riêng — xem `PO_MISA_AFTER_APPROVE_HINT`.
 */
export const PO_FIELDS_EDITABLE_AFTER_APPROVE =
  'Tên trên hóa đơn · Ngày dự kiến có hàng · Kho nhận mặc định · Ghi chú · Ngày giao chứng từ cho KT · Giao hàng nhiều lần'

/**
 * Mã đơn MISA không nằm trong popup dòng mà ở khối Thông tin chung, nên nhắc gộp
 * vào danh sách trên là chỉ sai chỗ — người dùng mở bút chì rồi tìm không ra.
 */
export const PO_MISA_AFTER_APPROVE_HINT =
  ' Riêng Mã đơn MISA sửa thẳng ở khối Thông tin chung phía trên.'

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
