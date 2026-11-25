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
  /** Lọc nâng cao của bảng sản phẩm — làm ở máy chủ, KPI không đổi, Xuất Excel + bản in theo cùng bộ lọc. */
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

/** Bộ lọc xu hướng của tab Tổng hợp theo sản phẩm (mã chữ của URL, khác mã số `CostTrend` của dòng). */
export type PackagingOverviewTrend = 'all' | 'up' | 'down' | 'flat' | 'missing'

/** Số sản phẩm theo xu hướng — trên tập đã lọc `q`, chưa lọc `trend` (chip luôn đủ số). */
export type PackagingOverviewCounts = Record<PackagingOverviewTrend, number>

/** Tham số của Tổng hợp theo sản phẩm — cũng là tham số của đường xuất Excel (cùng thứ tự). */
export interface PackagingOverviewParams {
  q?: string
  trend?: PackagingOverviewTrend
  sort_by?: string
  sort_dir?: 'asc' | 'desc'
  page?: number
  page_size?: number
  /** Lọc nâng cao: máy chủ lọc sau khi tính chi phí, số đếm chip theo cả các bộ lọc này. */
  /** Vai trò (1..5) cách nhau dấu phẩy, vd "1,5": sản phẩm có MÃ ở một trong các vai trò đó. */
  part_roles?: string
  carton_qty_min?: number
  carton_qty_max?: number
  cost_old_bottle_min?: number
  cost_old_bottle_max?: number
  cost_new_bottle_min?: number
  cost_new_bottle_max?: number
  diff_bottle_min?: number
  diff_bottle_max?: number
  diff_carton_min?: number
  diff_carton_max?: number
  /** Đơn vị %, so với số một chữ số lẻ đang hiện ở cột "% chênh". */
  pct_min?: number
  pct_max?: number
  warnings_only?: boolean
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

/** Số liệu tổng hợp của màn Tác động (ba thẻ trên màn hình / bản in). */
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
  /** Số sản phẩm sau lọc `q` + lọc nâng cao — tổng của bảng phân trang (khác `kpis.affected_products` là số chưa lọc). */
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
  /** Nguồn báo giá (bộ mã `quote_source_type`): 1 = nhập tay (`source_id` 0), 2 = nhập Excel (`source_id` = id đợt nhập). Máy chủ ghi. */
  source_type?: number
  source_id?: number
  source_label?: string
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

/** Chế độ chọn của tab Lịch sử mua hàng: theo mã VTBB, hoặc theo mã sản phẩm (mở rộng qua định mức). */
export type PackagingHistoryMode = 'code' | 'product'

/** Một lần mua (`GET /history` → `items[]`) — chụp bất biến của sổ giá, không sửa được. */
export interface PackagingHistoryRow {
  /** Id dòng sổ giá (khóa dòng của bảng). */
  id: number
  date: string | null
  code: string
  name: string
  group: string
  supplier_code: string
  /** Tên nhà cung cấp đã bỏ đuôi " - VTBB"; không có tên thì là mã; không có nhà cung cấp thì rỗng. */
  supplier: string
  /** Tên kho nhập hàng của lần mua (chép theo dòng sổ giá); rỗng = không biết kho. */
  warehouse: string
  qty: number | null
  unit: string
  /** VNĐ chưa VAT; 0 = dòng không có giá (không tính vào KPI / biểu đồ). */
  price: number | null
  vat: number | null
  /**
   * GIÁ TRỊ MUA của lần mua (VNĐ, chưa VAT): thành tiền Misa khi có, không thì giá x số lượng; null ở dòng đơn giá 0.
   * Tổng giá trị mua + giá bình quân gia quyền của `stats` cộng đúng số này.
   */
  amount: number | null
  /** Mã `PriceSourceType`: 1 = lịch sử cũ nạp Excel, 2 = dòng ĐMH của ERP (đang mở lẫn đã chốt), 3 = sổ Misa. */
  source_type: number
  /** Mã `LedgerLineStage`: 1 = đang mở, 2 = đã chốt. */
  line_stage: number
  /** Dòng ĐMH còn đang mở (giá có thể còn đổi): giao diện hiện nhãn "ĐMH đang mở". */
  is_open: boolean
  /** Id ĐMH nguồn; 0 = dữ liệu cũ không có ĐMH. */
  doc_id: number
  po_code: string
  /** Giá lần mua CÓ GIÁ liền trước của cùng mã (không phụ thuộc bộ lọc) và chênh / tỷ số so với nó. */
  prev_price: number | null
  diff: number | null
  pct: number | null
  /** Lần mua của mã trên TOÀN BỘ lịch sử (không phụ thuộc bộ lọc): 1 = lần mua GẦN NHẤT, như bản mẫu HTML. */
  seq: number
  /** Chế độ sản phẩm: sản phẩm của dòng (mỗi lần mua ra một dòng cho mỗi sản phẩm dùng mã); chế độ mã: rỗng. */
  hh_code: string
  hh_name: string
  /** Chế độ sản phẩm: mã `PackagingRole` của thành phần (chai / nắp / nhãn / nhãn thùng / thùng); chế độ mã: null. */
  role: number | null
}

export interface PackagingHistoryStats {
  purchase_count: number
  priced_count: number
  qty_total: number | null
  /** Giá bình quân GIA QUYỀN = tổng tiền / tổng số lượng của các lần mua có giá; null nếu chưa có số lượng. */
  weighted_avg: number | null
  min: number | null
  max: number | null
  supplier_count: number
  first_date: string | null
  last_date: string | null
  /** Tổng GIÁ TRỊ MUA (thành tiền Misa, không thì giá x số lượng) của các lần mua CÓ GIÁ. */
  amount_total: number | null
  /** Số mã có lần mua trong tập lọc. */
  code_count: number
  /** Chế độ sản phẩm: số sản phẩm có định mức trong phạm vi chọn (thẻ "Số sản phẩm"); chế độ mã: 0. */
  product_count: number
  /** ĐVT trên sổ giá (có nghĩa khi xem một mã). */
  unit: string
  /** Giá của lần mua có giá đầu tiên / gần nhất trong tập lọc. */
  first_price: number | null
  last_price: number | null
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
  /** Chỉ khi đúng MỘT mã được chọn: các điểm giá cũ → mới cho biểu đồ. */
  series: PackagingHistoryPoint[] | null
  suppliers: PackagingLastPricesSupplier[]
}

/** Bộ lọc của Lịch sử mua hàng — cũng là tham số của đường xuất Excel (cùng thứ tự). */
export interface PackagingHistoryParams {
  mode: PackagingHistoryMode
  /** Mã VTBB (chế độ `code`); rỗng = mọi mã VTBB của cụm giá. */
  codes?: string[]
  /** Mã sản phẩm (chế độ `product`); rỗng = mọi sản phẩm có định mức. */
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

/** Sản phẩm có định mức cho ô chọn của chế độ sản phẩm (`GET /hh-options`). */
export interface PackagingHhOption {
  code: string
  name: string
}
