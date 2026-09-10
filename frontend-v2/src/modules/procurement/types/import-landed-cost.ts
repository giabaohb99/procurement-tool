/**
 * Báo cáo GIÁ VỐN LÔ HÀNG NHẬP KHẨU (bao-CR-347 ở bản v1, bao-CR-357 dời sang v2).
 *
 * Backend gom cả hai cách nhìn — theo LÔ HÀNG và theo DÒNG HÀNG — vào MỘT lần gọi
 * `/api/reports/import-landed-cost`, nên đổi cách nhìn trên màn hình không phải gọi lại.
 *
 * Số liệu tính tại thời điểm xem, không lưu lại ở đâu cả.
 */

/** Hai cách nhìn cùng một bộ số liệu. */
export type LandedCostView = 'orders' | 'items'

export const LANDED_COST_VIEWS: { value: LandedCostView; label: string }[] = [
  { value: 'orders', label: 'Theo lô hàng' },
  { value: 'items', label: 'Chi tiết theo dòng hàng' },
]

export function landedCostViewLabel(view: LandedCostView): string {
  return LANDED_COST_VIEWS.find((item) => item.value === view)?.label || ''
}

/**
 * Một loại chi phí nhập khẩu có mặt trong phạm vi đang lọc.
 *
 * `no` là số mục in trên báo cáo ("2.1", "2.2"…), `code` là mã số của loại chi phí —
 * cũng chính là KHÓA (dạng chuỗi) trong `by_type`.
 */
export interface LandedCostType {
  code: number
  no: string
  label: string
}

/** Phần số liệu mà cột từng đơn và cột TỔNG dùng chung — bảng xoay dọc đọc chung một khuôn. */
export interface LandedCostAmounts {
  qty_total: number
  weight_total: number
  currency: string
  /** Nhiều đồng tiền trong cùng phạm vi: `goods_amount` khi đó về 0 vì cộng lại vô nghĩa. */
  currency_mixed: boolean
  goods_amount: number
  goods_base: number
  by_type: Record<string, number>
  cost_total: number
  landed_total: number
  price_per_kg: number
}

export interface LandedCostOrderRow extends LandedCostAmounts {
  po_id: number
  code: string
  order_date: string
  etd_date: string
  status: string
  status_label: string
  note: string
  supplier_code: string
  supplier_name: string
  customs_decl_no: string
  customs_decl_date: string
  exchange_rate: number
}

export interface LandedCostTotals extends LandedCostAmounts {
  order_count: number
}

export interface LandedCostItemRow {
  po_id: number
  code: string
  etd_date: string
  status_label: string
  item_id: number
  product_code: string
  product_name: string
  unit: string
  qty_order: number
  weight_kg: number
  goods_base: number
  by_type: Record<string, number>
  cost_base: number
  landed_base: number
  price_per_unit: number
  price_per_kg: number
}

/**
 * Dòng TỔNG của cách nhìn theo dòng hàng.
 *
 * Cố ý KHÔNG có `price_per_unit`: mỗi dòng một đơn vị tính, cộng cái đó lại thì ra
 * một con số không có nghĩa gì.
 */
export interface LandedCostItemTotals {
  line_count: number
  qty_order: number
  weight_kg: number
  goods_base: number
  by_type: Record<string, number>
  cost_base: number
  landed_base: number
  price_per_kg: number
}

export interface LandedCostReport {
  cost_types: LandedCostType[]
  orders: LandedCostOrderRow[]
  totals: LandedCostTotals
  items: LandedCostItemRow[]
  item_totals: LandedCostItemTotals
  warnings: string[]
}

/** Bộ lọc người dùng gõ trên màn hình. */
export interface LandedCostFilter {
  codes: string
  date_from: string
  date_to: string
}

/**
 * Tham số thật sự gửi lên API (đã bỏ ô rỗng).
 *
 * Khai bằng `type` chứ không phải `interface`: hàm dựng khóa cache nhận
 * `Record<string, unknown>`, mà interface KHÔNG tự có chữ ký chỉ mục ngầm.
 */
export type LandedCostParams = {
  codes?: string
  date_from?: string
  date_to?: string
  company_id?: string
}

/**
 * Dựng tham số gọi API.
 *
 * Mã đơn ĐÈ khoảng ngày: gõ mã đơn nghĩa là muốn đúng mấy lô đó, bất kể chúng đặt
 * ngày nào — gửi kèm khoảng ngày thì lô ngoài khoảng biến mất một cách khó hiểu.
 */
export function buildLandedCostParams(
  filter: LandedCostFilter,
  companyId?: string,
): LandedCostParams {
  const params: LandedCostParams = {}
  const codes = filter.codes
    .split(',')
    .map((code) => code.trim())
    .filter(Boolean)
    .join(',')

  if (codes) {
    params.codes = codes
  } else {
    if (filter.date_from) params.date_from = filter.date_from
    if (filter.date_to) params.date_to = filter.date_to
  }
  if (companyId) params.company_id = companyId
  return params
}
