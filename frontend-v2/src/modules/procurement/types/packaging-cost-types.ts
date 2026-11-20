/**
 * duoc-CR-784 — kiểu dữ liệu của cụm Giá bao bì (Tác động giá, Bảng giá VTBB, Báo giá, Định mức).
 *
 * Bám hợp đồng API ở `doc/erp/thu-mua/plans/261120-tac-dong-gia-bao-bi/phase-04-...md` (prefix
 * `/api/packaging-cost`) và ba router CRUD của phase 03. Mọi số tiền là VNĐ CHƯA VAT; `null` nghĩa là
 * "chưa có giá" (khác 0). Trạng thái / vai trò / cảnh báo là MÃ SỐ — nhãn tra ở bộ mã sinh TS
 * (`utils/packaging-warning-text.ts`), không gửi câu tiếng Việt qua API.
 */

/** Một cảnh báo của dòng: `kind` = mã `CostWarning`, `role` = mã `PackagingRole` khi cảnh báo gắn với một thành phần. */
export interface PackagingWarning {
  kind: number
  role?: number | null
}

/** Mã bao bì cho ô chọn nhiều (`GET /code-options`) — chỉ mã đang dùng trong định mức. */
export interface PackagingCodeOption {
  code: string
  name: string
  group: string
  /** Số sản phẩm (mã HH) đang dùng mã này. */
  usage: number
  /** Giá mới theo bảng giá; `null` = chưa có giá. */
  new: number | null
}

/** Thân của `POST /impact` và `POST /impact/export`. */
export interface PackagingImpactRequest {
  codes: string[]
  /** Giá giả định theo mã — chỉ gửi mã có giá; bỏ mã khỏi đây = dùng giá bảng giá. */
  assumed_prices?: Record<string, number>
  date_from?: string
  date_to?: string
  /**
   * Bảng sản phẩm bị ảnh hưởng phân trang / tìm / xếp tại MÁY CHỦ (luật §8); KPI luôn tính trên toàn bộ tập.
   * Xuất Excel bỏ qua `page` / `page_size` nhưng theo `q` + `sort_by` / `sort_dir`.
   */
  page?: number
  page_size?: number
  sort_by?: string
  sort_dir?: 'asc' | 'desc'
  /** Tìm theo mã HH, tên, tên pháp lý, mã thành phần (không phân biệt dấu). */
  q?: string
}

/** Một mã đã chọn ở bảng trên của màn Tác động. */
export interface PackagingSelectedCode {
  code: string
  name: string
  group: string
  unit: string
  old: number | null
  new: number | null
  assumed: number | null
  /** Giá đang dùng để tính = giả định nếu có, không thì `new`. */
  applied: number | null
  diff: number | null
  /** TỶ SỐ chênh / giá cũ (0.125 = 12,5%) — máy chủ trả 6 số lẻ. */
  pct: number | null
  usage: number
  min: number | null
  max: number | null
  floor: number | null
  ceiling: number | null
  warnings?: (number | PackagingWarning)[]
}

/** Một thành phần (chai / nắp / nhãn / nhãn thùng / thùng) của một sản phẩm. */
export interface PackagingPart {
  /** Mã `PackagingRole`: 1 chai, 2 nắp, 3 nhãn, 4 nhãn thùng, 5 thùng. */
  role: number
  /** Rỗng = sản phẩm không có thành phần này. */
  code: string
  name?: string
  old: number | null
  new: number | null
  applied: number | null
  /** Mã này nằm trong danh sách đang chọn — tô nổi ô. */
  selected: boolean
}

/** Một sản phẩm bị ảnh hưởng (bảng dưới của màn Tác động). */
export interface PackagingImpactProduct {
  hh_code: string
  hh_name: string
  legal_name?: string
  carton_qty: number
  parts: PackagingPart[]
  cost_old_bottle: number | null
  cost_new_bottle: number | null
  cost_applied_bottle: number | null
  diff_bottle: number | null
  pct: number | null
  cost_old_carton: number | null
  cost_applied_carton: number | null
  diff_carton: number | null
  /** Mã `CostTrend`. */
  trend: number
  warnings: PackagingWarning[]
}

/** Bốn thẻ KPI của màn Tác động. */
export interface PackagingImpactKpis {
  selected_count: number
  selected_by_group: Record<string, number>
  assumed_count: number
  affected_products: number
  increased: number
  decreased: number
  max_increase_carton: number | null
  max_increase_bottle: number | null
}

export interface PackagingImpactResult {
  selected: PackagingSelectedCode[]
  kpis: PackagingImpactKpis
  /** CHỈ trang được hỏi (đã lọc `q`, đã xếp). */
  products: PackagingImpactProduct[]
  /** Số sản phẩm sau lọc `q` — tổng của bảng phân trang (khác `kpis.affected_products` là số chưa lọc). */
  products_total: number
}

export interface PackagingQuoteInfo {
  price: number
  valid_from: string
  supplier_code?: string
}

/** Một dòng của Bảng giá VTBB (`GET /price-list`). */
export interface PackagingPriceRow {
  code: string
  name: string
  group: string
  unit: string
  purchase_count: number
  last_date: string | null
  /** Lần mua CÓ GIÁ gần nhất và lần trước đó (bỏ dòng đơn giá 0), cùng luật với giá cũ / mới. */
  last_purchase_price: number | null
  last_purchase_date: string | null
  prev_purchase_price: number | null
  quote: PackagingQuoteInfo | null
  /** Bản phẳng của `quote` để xếp tại máy chủ (`sort_by=quote_price|quote_from`). */
  quote_price?: number | null
  quote_from?: string | null
  old: number | null
  new: number | null
  diff: number | null
  pct: number | null
  usage: number
  min: number | null
  max: number | null
  floor: number | null
  ceiling: number | null
  warnings?: (number | PackagingWarning)[]
}

export interface PackagingPriceListResult {
  items: PackagingPriceRow[]
  total: number
}

/** Bộ lọc của Bảng giá VTBB — cũng là tham số của đường xuất Excel (cùng thứ tự). */
export interface PackagingPriceListParams {
  q?: string
  group?: string
  scope?: 'bom' | 'all'
  breach_only?: boolean
  date_from?: string
  date_to?: string
  sort_by?: string
  sort_dir?: 'asc' | 'desc'
  page?: number
  page_size?: number
}

/** Một lần mua trong ma trận Giá mua gần nhất (`purchases[]`, lần gần nhất đứng đầu). */
export interface PackagingLastPurchase {
  date: string | null
  supplier_code: string
  /** Tên nhà cung cấp đã bỏ đuôi " - VTBB"; không có tên thì là mã. */
  supplier: string
  qty: number | null
  price: number | null
}

/** Một dòng của tab Giá mua gần nhất (`GET /last-prices`) — một mã VTBB. */
export interface PackagingLastPricesRow {
  code: string
  name: string
  group: string
  unit: string
  /** Số lần mua CÓ GIÁ (> 0) trong khoảng ngày đang lọc — không chỉ `n` lần đang hiện. */
  purchase_count: number
  /** Tối đa `n` lần, lần gần nhất trước. */
  purchases: PackagingLastPurchase[]
  last_price: number | null
  last_date: string | null
  /** Tỷ số biến động lần 1 so lần 2 / lần `n` (0,05 = +5%); thiếu lần so sánh thì null. */
  v12: number | null
  v1n: number | null
  /** Giá trung bình của các lần đang hiện. */
  avg: number | null
}

export interface PackagingLastPricesGroup {
  group: string
  count: number
}

export interface PackagingLastPricesSupplier {
  code: string
  name: string
}

export interface PackagingLastPricesResult {
  items: PackagingLastPricesRow[]
  total: number
  /** Số mã mỗi nhóm (chưa áp ô tìm / nhóm / nhà cung cấp / biến động) theo đúng thứ tự chip. */
  groups: PackagingLastPricesGroup[]
  /** Nhà cung cấp có trong các lần mua đang hiện — nguồn của ô chọn nhiều. */
  suppliers: PackagingLastPricesSupplier[]
}

export type LastPricesTrend = 'all' | 'up' | 'down' | 'flat'

/** Bộ lọc của tab Giá mua gần nhất — cũng là tham số của đường xuất Excel (cùng thứ tự). */
export interface PackagingLastPricesParams {
  /** Số lần mua hiển thị, 2–10 (mặc định 5). */
  n?: number
  q?: string
  group?: string
  /** Mã nhà cung cấp; mã có nhà cung cấp đó trong `n` lần đang hiện thì giữ. */
  supplier?: string[]
  date_from?: string
  date_to?: string
  trend?: LastPricesTrend
  /** |biến động lần 1 so lần 2| tối thiểu, đơn vị %. */
  min_pct?: number
  only_priced?: boolean
  bom_only?: boolean
  scope?: 'bom' | 'all'
  sort_by?: string
  sort_dir?: 'asc' | 'desc'
  page?: number
  page_size?: number
  /** Chỉ đường xuất Excel: thêm cột Số lượng mỗi lần mua. */
  show_qty?: boolean
}

/** Báo giá của NCC (`/api/product-price-quotes`). */
export interface PackagingQuote extends Record<string, unknown> {
  id: number
  product_code: string
  /** Gắn ở `enrich_out` của máy chủ (tên + ĐVT từ danh mục, tên NCC). */
  product_name?: string
  product_unit?: string
  supplier_code: string
  supplier_name?: string
  price: number
  vat: number
  valid_from: string
  note: string
  updated_at?: string
}

/** Ngưỡng giá sàn / trần một mã (`/api/product-price-limits`). */
export interface PackagingPriceLimit {
  id: number
  product_code: string
  floor_price: number | null
  ceiling_price: number | null
  note: string
}

/** Định mức bao bì một mã HH (`/api/packaging-boms`). */
export interface PackagingBom extends Record<string, unknown> {
  id: number
  hh_code: string
  hh_name: string
  legal_name: string
  bottle_code: string
  cap_code: string
  label_code: string
  carton_label_code: string
  carton_code: string
  carton_qty: number
  /** Năm thành phần kèm tên + ĐVT danh mục; `in_catalog = false` = mã chưa có trong danh mục sản phẩm. */
  parts?: { role: number; code: string; name: string; unit: string; in_catalog: boolean }[]
  updated_at?: string
}
