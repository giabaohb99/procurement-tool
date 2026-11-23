/**
 * duoc-CR-784 — kiểu dữ liệu cụm Giá bao bì (bản v1), khớp API `/api/packaging-cost/*` ở backend
 * (`backend/app/modules/packaging_cost/`). Mọi số tiền là VNĐ CHƯA VAT; `null` = "chưa có giá" (khác 0).
 * Trạng thái / vai trò / cảnh báo là MÃ SỐ — nhãn tra ở `utils/packaging-price.ts`.
 */

/** Một cảnh báo của dòng: `kind` = mã `CostWarning`, `role` = mã `PackagingRole` khi gắn với một thành phần. */
export interface PackagingWarning { kind: number; role?: number | null }
export type PackagingWarningInput = number | PackagingWarning

/** Mã bao bì cho ô chọn nhiều (`GET /code-options`). */
export interface PackagingCodeOption {
  code: string
  name: string
  group: string
  usage: number
  new: number | null
}

/** Thân của `POST /impact` và `POST /impact/export`. */
export interface PackagingImpactRequest {
  codes: string[]
  assumed_prices?: Record<string, number>
  date_from?: string
  date_to?: string
  page?: number
  page_size?: number
  sort_by?: string
  sort_dir?: 'asc' | 'desc'
  q?: string
  /** Lọc nâng cao của bảng sản phẩm (máy chủ lọc; KPI không đổi; Xuất Excel + bản in theo cùng bộ lọc). */
  trend?: Exclude<PackagingOverviewTrend, 'all'>
  /** Vai trò (1..5) mà sản phẩm có MÃ ĐÃ CHỌN — một trong các vai trò. */
  part_roles?: number[]
  carton_qty_min?: number
  carton_qty_max?: number
  diff_bottle_min?: number
  diff_bottle_max?: number
  diff_carton_min?: number
  diff_carton_max?: number
  cost_new_bottle_min?: number
  cost_new_bottle_max?: number
  /** Chỉ sản phẩm đang có ít nhất một cảnh báo. */
  warnings_only?: boolean
}

export interface PackagingSelectedCode {
  code: string
  name: string
  group: string
  unit: string
  old: number | null
  new: number | null
  assumed: number | null
  applied: number | null
  diff: number | null
  /** TỶ SỐ chênh / giá cũ (0.125 = 12,5%). */
  pct: number | null
  usage: number
  min: number | null
  max: number | null
  floor: number | null
  ceiling: number | null
  warnings?: PackagingWarningInput[]
}

export interface PackagingPart {
  role: number
  code: string
  name?: string
  old: number | null
  new: number | null
  applied: number | null
  selected: boolean
}

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
  trend: number
  warnings: PackagingWarning[]
}

/** Bộ lọc xu hướng của tab Tổng hợp theo sản phẩm (mã chữ của URL, khác mã số `CostTrend` của dòng). */
export type PackagingOverviewTrend = 'all' | 'up' | 'down' | 'flat' | 'missing'
/** Số sản phẩm theo xu hướng — trên tập đã lọc `q`, chưa lọc `trend` (chip luôn đủ số). */
export type PackagingOverviewCounts = Record<PackagingOverviewTrend, number>

export interface PackagingOverviewParams {
  q?: string
  trend?: PackagingOverviewTrend
  sort_by?: string
  sort_dir?: 'asc' | 'desc'
  page?: number
  page_size?: number
}

export interface PackagingOverviewResult {
  /** Cùng hình với `products[]` của Tác động giá (giá giả định không có: `applied` = `new`). */
  items: PackagingImpactProduct[]
  /** Số dòng sau cả hai bộ lọc `q` + `trend`. */
  total: number
  counts: PackagingOverviewCounts
}

/** Sản phẩm tăng chi phí /thùng nhiều nhất (thẻ "Tăng nhiều nhất /thùng") — trên TOÀN BỘ tập bị ảnh hưởng, không theo bộ lọc. */
export interface PackagingMaxIncreaseProduct {
  hh_code: string
  hh_name: string
  diff_bottle: number | null
  diff_carton: number
  carton_qty: number
}

export interface PackagingImpactKpis {
  selected_count: number
  selected_by_group: Record<string, number>
  assumed_count: number
  affected_products: number
  increased: number
  decreased: number
  max_increase_carton: number | null
  max_increase_bottle: number | null
  /** `null` = không sản phẩm nào tăng chi phí /thùng (thẻ ghi "Không có sản phẩm tăng"). */
  max_increase_product: PackagingMaxIncreaseProduct | null
}

export interface PackagingImpactResult {
  selected: PackagingSelectedCode[]
  kpis: PackagingImpactKpis
  /** CHỈ trang được hỏi (đã lọc `q`, đã xếp). */
  products: PackagingImpactProduct[]
  /** Số sản phẩm sau lọc `q` — tổng của bảng phân trang. */
  products_total: number
}

export interface PackagingQuoteInfo { price: number; valid_from: string; supplier_code?: string }

/** Một dòng của Bảng giá VTBB (`GET /price-list`). */
export interface PackagingPriceRow {
  code: string
  name: string
  group: string
  unit: string
  purchase_count: number
  last_date: string | null
  last_purchase_price: number | null
  last_purchase_date: string | null
  prev_purchase_price: number | null
  quote: PackagingQuoteInfo | null
  old: number | null
  new: number | null
  diff: number | null
  pct: number | null
  usage: number
  min: number | null
  max: number | null
  floor: number | null
  ceiling: number | null
  warnings?: PackagingWarningInput[]
}

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

/** Một lần mua trong ma trận Giá mua gần nhất (lần gần nhất đứng đầu). */
export interface PackagingLastPurchase {
  date: string | null
  supplier_code: string
  supplier: string
  qty: number | null
  price: number | null
}

export interface PackagingLastPricesRow {
  code: string
  name: string
  group: string
  unit: string
  purchase_count: number
  purchases: PackagingLastPurchase[]
  last_price: number | null
  last_date: string | null
  /** Tỷ số biến động lần 1 so lần 2 / lần n (0,05 = +5%). */
  v12: number | null
  v1n: number | null
  avg: number | null
}

export interface PackagingSupplierOption { code: string; name: string }

export interface PackagingLastPricesResult {
  items: PackagingLastPricesRow[]
  total: number
  groups: { group: string; count: number }[]
  suppliers: PackagingSupplierOption[]
}

export type LastPricesTrend = 'all' | 'up' | 'down' | 'flat'

export interface PackagingLastPricesParams {
  n?: number
  q?: string
  group?: string
  supplier?: string[]
  date_from?: string
  date_to?: string
  trend?: LastPricesTrend
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

export type PackagingHistoryMode = 'code' | 'product'

export interface PackagingHistoryRow {
  id: number
  date: string | null
  code: string
  name: string
  group: string
  supplier_code: string
  supplier: string
  /** Tên kho nhập hàng của lần mua (chép theo dòng sổ giá); rỗng = không biết kho. */
  warehouse: string
  qty: number | null
  unit: string
  price: number | null
  vat: number | null
  amount: number | null
  /** Mã `PriceSourceType`: 1 = lịch sử mua, 2 = dòng ĐMH đang mở. */
  source_type: number
  doc_id: number
  po_code: string
  prev_price: number | null
  diff: number | null
  pct: number | null
  seq: number
  roles: number[]
}

export interface PackagingHistoryStats {
  purchase_count: number
  priced_count: number
  qty_total: number | null
  weighted_avg: number | null
  min: number | null
  max: number | null
  supplier_count: number
  first_date: string | null
  last_date: string | null
}

export interface PackagingHistoryPoint {
  date: string
  price: number
  supplier_code: string
  supplier: string
  qty: number | null
}

export interface PackagingHistoryResult {
  items: PackagingHistoryRow[]
  total: number
  stats: PackagingHistoryStats
  /** Chỉ khi đúng MỘT mã được chọn. */
  series: PackagingHistoryPoint[] | null
  suppliers: PackagingSupplierOption[]
}

export interface PackagingHistoryParams {
  mode: PackagingHistoryMode
  codes?: string[]
  hh_codes?: string[]
  q?: string
  supplier?: string[]
  date_from?: string
  date_to?: string
  sort_by?: string
  sort_dir?: 'asc' | 'desc'
  page?: number
  page_size?: number
}

export interface PackagingHhOption { code: string; name: string }

/** Ngưỡng giá sàn / trần một mã (`/api/product-price-limits`). */
export interface PackagingPriceLimit {
  id: number
  product_code: string
  floor_price: number | null
  ceiling_price: number | null
  note: string
}
