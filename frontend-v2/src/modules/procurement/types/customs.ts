// bao-CR-470 — kiểu dữ liệu của màn Tra cứu giá hải quan (bản v2).
//
// Khớp đúng hình dạng trả về của `backend/app/modules/customs/service.py` +
// `controller.py`. Một «dòng hàng» là MỘT dòng của tệp GTT02, không phải cả tờ khai:
// tệp không có số tờ khai (xem doc/erp/hai-quan/02-thiet-ke-ky-thuat.md §2.2).

/** Bộ lọc dùng chung cho mọi thẻ của màn — nằm trên URL, rỗng = không lọc. */
export interface CustomsFilters {
  q: string
  hs_code: string
  origin: string
  unit: string
  formulation: string
  /** bao-CR-493: nhiều id nối bằng dấu phẩy («12,34») — backend tự tách, nhiều là HOẶC. */
  importer_id: string
  partner_id: string
  date_from: string
  date_to: string
  /** bao-CR-493 — sáu ô lọc thêm theo sheet 4 của yêu cầu phòng Thu mua. Chuỗi rỗng = không lọc. */
  currency: string
  incoterm: string
  batch_id: string
  price_min: string
  price_max: string
  qty_min: string
  qty_max: string
  rate_min: string
  rate_max: string
}

/** Một dòng hàng — đủ 32 cột của tệp gốc + vài trường suy ra. */
export type CustomsLine = {
  id: number
  batch_id: number
  source_row: number
  date_fixed: boolean
  importer_id: number | null
  partner_id: number | null
  active_ingredient: string
  formulation: string
  reg_date: string | null
  office_code: string
  line_no: number | null
  import_country: string
  importer_name: string
  importer_tax_code: string
  partner_name: string
  origin_country: string
  product_name: string
  hs_code: string
  quantity: number | null
  unit_code: string
  price_usd: number | null
  adj_price_usd: number | null
  effective_price_usd: number | null
  /** bao-CR-493 — giá hiệu lực × tỷ giá USD × 1,07 (thuế NK 7% tạm tính), tròn đồng. */
  price_vnd_flat: number | null
  /** bao-CR-493 — giá hiệu lực × tỷ giá USD × (1 + thuế suất XNK của dòng); thiếu thuế suất thì null. */
  price_vnd_line_tax: number | null
  price_nt: number | null
  adj_price_nt: number | null
  currency: string
  fx_rate: number | null
  usd_rate: number | null
  contract_no: string
  contract_date: string | null
  incoterm: string
  transport_mode: string | number | null
  transport_label?: string
  rate_import: number | null
  rate_excise: number | null
  rate_vat: number | null
  rate_safeguard: number | null
  tax_import: number | null
  tax_excise: number | null
  tax_vat: number | null
  tax_environment: number | null
  tax_safeguard: number | null
}

export interface CustomsLineList {
  total: number
  items: CustomsLine[]
}

/** Dải tháng đã phủ đầu trang. */
export interface CustomsCoverage {
  total: number
  date_from: string | null
  date_to: string | null
  last_import_at: string | null
  years: { year: number; months: number[] }[]
}

export interface CustomsOptionItem {
  value: string
  count: number
  /** Nhãn hiện thay cho `value` (ô lọc lô nạp: «#12 1.xls»). */
  label?: string
}

export interface CustomsOptions {
  hs_codes: CustomsOptionItem[]
  origins: CustomsOptionItem[]
  units: CustomsOptionItem[]
  ingredients: CustomsOptionItem[]
  formulations: CustomsOptionItem[]
  /** bao-CR-493 */
  currencies?: CustomsOptionItem[]
  incoterms?: CustomsOptionItem[]
  batches?: CustomsOptionItem[]
  ingredient_coverage: { total: number; tagged: number; ratio: number | null }
}

export interface CustomsUnitCount {
  unit: string
  count: number
}

/**
 * Một kỳ trên biểu đồ. Kỳ trống vẫn có mặt với `count = 0` và giá `null`.
 *
 * `p25` · `p75` = khoảng của NỬA số dòng ở giữa ("khoảng giá phổ biến") — dải tô trên
 * biểu đồ dùng khoảng này chứ không dùng thấp–cao: vài dòng giá lạ (250 USD/lít giữa đám
 * 2–4 USD/lít) kéo trục lên trần và ép đường bình quân dẹp sát đáy.
 */
export interface CustomsSeriesPoint {
  period: string
  label: string
  count: number
  qty: number
  min: number | null
  max: number | null
  p25?: number | null
  median?: number | null
  p75?: number | null
  wavg: number | null
  low_data: boolean
}

export interface CustomsKpi {
  count?: number
  qty?: number
  min?: number | null
  max?: number | null
  p25?: number | null
  median?: number | null
  p75?: number | null
  /** Số dòng giá bất thường theo luật hộp râu 1,5 × IQR — chỉ đếm, không loại khỏi số liệu. */
  outliers?: number
  wavg?: number | null
}

export type CustomsPeriod = 'month' | 'quarter' | 'year'
export type CustomsPriceMode = 'adjusted' | 'declared'

export interface CustomsStats {
  period: CustomsPeriod
  price_mode: CustomsPriceMode
  unit: string
  units: CustomsUnitCount[]
  series: CustomsSeriesPoint[]
  kpi: CustomsKpi
  best_period: string | null
  min_lines_for_best: number
  coverage: {
    lines: number
    months: number
    years: number
    date_from: string | null
    date_to: string | null
    empty_periods: string[]
  }
}

export interface CustomsCompareTerm {
  term: string
  series: CustomsSeriesPoint[]
  kpi: CustomsKpi
}

export interface CustomsCompare {
  period: CustomsPeriod
  unit: string
  units: CustomsUnitCount[]
  terms: CustomsCompareTerm[]
}

export interface CustomsImporterRow {
  importer_id: number
  name: string
  tax_code: string
  count: number
  qty: number
  share: number | null
  wavg: number | null
  last_date: string | null
}

export interface CustomsImporters {
  unit: string
  units: CustomsUnitCount[]
  total_importers: number
  items: CustomsImporterRow[]
}

/** Một mục pháp lý — dùng cho cả cảnh báo lẫn kết quả tra cứu. */
export interface CustomsRegulationHit {
  id: number
  list_code: number
  list_label: string
  name: string
  name_vi: string
  cas_no: string
  category: string
  threshold_kg: number | null
  banned_year: number | null
  legal_basis: string
  note: string
  obligation: string
}

export interface CustomsRegulationLookup {
  term: string
  formula_cas: string | null
  items: CustomsRegulationHit[]
}

export interface CustomsTariffRow {
  hs_code: string
  name_vn: string
  name_en: string
  unit: string
  rate_normal: string | number | null
  rate_mfn: string | number | null
  rate_vat: string | number | null
  fta: Record<string, string | number | null>
  policy: string
}

/** Trạng thái lô nạp — khớp `ImportStatus` của backend. */
export const CUSTOMS_BATCH_STATUS = {
  queued: 0,
  running: 1,
  done: 2,
  failed: 3,
  reverted: 4,
} as const

/** Loại lô — khớp `ImportMode` của backend. */
export const CUSTOMS_BATCH_MODE = {
  dryRun: 0,
  apply: 1,
} as const

export interface CustomsImportBatch {
  id: number
  mode: number
  status: number
  filename: string
  file_size: number
  /** bao-CR-493 — lô nạp qua màn hình có tệp gốc để tải lại; lô nạp bằng script thì không. */
  has_file?: boolean
  total_rows: number
  created_count: number
  deleted_count: number
  skipped_count: number
  warning_count: number
  error_count: number
  error_summary: string | null
  date_from: string
  date_to: string
  date_fixed: number
  created_at: string | null
  created_by: number | null
  created_by_name: string | null
  started_at: string | null
  finished_at: string | null
}

export interface CustomsImportBatchList {
  total: number
  items: CustomsImportBatch[]
}

export interface CustomsBatchLog {
  id: number
  row_no: number | null
  level: number
  message: string
}

export interface CustomsBatchLogList {
  total: number
  items: CustomsBatchLog[]
}

/** Bản ghi danh mục hóa chất theo văn bản (`/api/customs-regulations`). */
export type CustomsRegulation = {
  id: number
  list_code: number
  name: string
  name_vi: string
  cas_no: string
  category: string
  threshold_kg: number | null
  banned_year: number | null
  legal_basis: string
  note: string
  is_active: boolean
}
