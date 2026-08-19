import type { PermissionEntity } from '@/core/authorization/permission-types'

/** Kỳ "cả năm" — giá trị mặc định của ô "Xem theo" và của `metricValue`. */
export const ALL_PERIOD = 'all'

/** Một mốc tháng do backend trả: `key` để tra số, `label` để hiện ra. */
export interface ReportMonth {
  key: string
  label: string
}

/** Một cột số liệu của bảng báo cáo. */
export interface ReportMetric {
  key: string
  label: string
  /** Hiện kèm dấu %. Không đặt = số đếm hoặc số tiền. */
  pct?: boolean
}

/** Ô số liệu của MỘT tháng, vd `{ trans: 12, late: 3, rate: 25 }`. */
export type MetricCell = Record<string, number>

/**
 * Một dòng ma trận báo cáo.
 *
 * `key` là TÊN đối tượng (tên NCC, tên bộ phận, tên phân loại…) chứ không phải
 * id: backend gom nhóm theo cột tên trên ĐMH (`po.department`, `po.nspt`,
 * `po.supplier_code`, `item.item_group`). Xem N-008 trong change-log — đổi sang
 * gom theo id còn phải chờ backfill `department_id` / `nspt_id`.
 *
 * Số liệu nằm ở hai tầng: `row[metric]` = tổng cả năm, `row.m['2026-08'][metric]`
 * = riêng tháng đó. Tháng không phát sinh thì KHÔNG có khóa trong `m`.
 */
export interface MatrixRow {
  key: string
  m?: Record<string, MetricCell>
  [metric: string]: unknown
}

/** Cột tỷ lệ (trễ / gấp) — chỉ số duy nhất được tô cảnh báo. */
export const RATE_METRIC = 'rate'
/** Vượt ngưỡng này thì dòng bị tô đỏ. Bê nguyên ngưỡng của bản v1. */
export const WARN_RATE = 30

/**
 * Đọc một ô số liệu, che luôn hai tầng dữ liệu và các tháng khuyết.
 *
 * `period === 'all'` -> tổng cả năm nằm thẳng trên dòng; ngược lại đọc trong
 * `m[period]`. Thiếu ở đâu cũng trả 0 chứ không trả `undefined`: bảng báo cáo
 * luôn phải hiện số, ô trống dễ bị hiểu là "chưa tải xong".
 */
export function metricValue(row: MatrixRow, metric: string, period: string): number {
  const raw = period === ALL_PERIOD ? row[metric] : row.m?.[period]?.[metric]
  const num = Number(raw ?? 0)
  return Number.isFinite(num) ? num : 0
}

/** Dòng có bị tô cảnh báo không (tỷ lệ trễ / gấp vượt ngưỡng). */
export function isWarnRow(row: MatrixRow, period: string, warnMetric?: string): boolean {
  if (!warnMetric) return false
  return metricValue(row, warnMetric, period) > WARN_RATE
}

/** Khóa sắp xếp của cột TÊN — không phải một chỉ số nên phải có khóa riêng. */
export const NAME_SORT_KEY = '__name__'

export type SortDir = 'asc' | 'desc'

export interface ReportSort {
  key: string
  dir: SortDir
}

/**
 * Vòng sắp xếp khi bấm vào header: cột mới -> giảm dần; cùng cột: giảm -> tăng
 * -> BỎ sắp xếp (về đúng thứ tự backend trả, thường là theo độ lớn).
 */
export function nextSort(current: ReportSort | null, key: string): ReportSort | null {
  if (!current || current.key !== key) return { key, dir: 'desc' }
  return current.dir === 'desc' ? { key, dir: 'asc' } : null
}

/**
 * Rút gọn số tiền cho trục biểu đồ: 286.000.000 -> "286 tr".
 *
 * Chỉ dùng cho NHÃN TRỤC và tooltip biểu đồ. Số trong bảng luôn ghi đủ chữ số
 * bằng `formatMoney` — báo cáo là để đối chiếu, không được làm tròn ngầm.
 */
export function shortMoney(value: number): string {
  const num = Number(value || 0)
  if (num >= 1e9) return `${trimTrailingZero(num / 1e9)} tỷ`
  if (num >= 1e6) return `${trimTrailingZero(num / 1e6)} tr`
  if (num >= 1e3) return `${Math.round(num / 1e3)}k`
  return String(num)
}

function trimTrailingZero(num: number): string {
  return num.toFixed(1).replace(/\.0$/, '')
}

/** Một tab của màn báo cáo. */
export interface ReportTab {
  key: string
  label: string
  /**
   * Không có quyền đọc thực thể này thì ẩn hẳn tab. Backend cũng tự chặn
   * (`_can_see_ncc` trả mảng rỗng), đây chỉ là lớp che cho đỡ hiện tab trống.
   */
  need?: PermissionEntity
}

/**
 * Tám tab của báo cáo mua hàng.
 *
 * Ba tab gắn `purchase_order` là dữ liệu phía THU MUA (NCC, nhân sự phụ trách,
 * chi phí vận chuyển): phòng ban yêu cầu không được xem. Tab "Bộ phận" thì ai
 * cũng vào được nhưng backend cắt dòng theo `report_dept_scope` — phòng ban chỉ
 * thấy phòng mình.
 */
export const REPORT_TABS: ReportTab[] = [
  { key: 'overview', label: 'Tổng quan' },
  { key: 'supplier', label: 'Nhà cung cấp', need: 'purchase_order' },
  { key: 'item_group', label: 'Phân loại vật tư bao bì / nguyên liệu' },
  { key: 'nspt', label: 'Nhân sự phụ trách', need: 'purchase_order' },
  { key: 'department', label: 'Bộ phận (đơn gấp)' },
  { key: 'shipping', label: 'Chi phí vận chuyển', need: 'purchase_order' },
  { key: 'pyc_req', label: 'Yêu cầu mua hàng', need: 'purchase_request' },
  { key: 'ycks_req', label: 'Yêu cầu báo giá', need: 'survey_request' },
]

export const SUPPLIER_METRICS: ReportMetric[] = [
  { key: 'trans', label: 'Số lần giao dịch' },
  { key: 'late', label: 'Số lần trễ' },
  { key: 'rate', label: 'Tỷ lệ trễ', pct: true },
]

export const ITEM_GROUP_METRICS: ReportMetric[] = [
  { key: 'trans', label: 'Số lần mua' },
  { key: 'cost', label: 'Tổng chi phí mua' },
]

export const NSPT_METRICS: ReportMetric[] = [
  { key: 'orders', label: 'Số lần giao' },
  { key: 'late', label: 'Trễ quy định' },
  { key: 'ontime', label: 'Đúng hạn' },
  { key: 'early', label: 'Giao sớm' },
  { key: 'rate', label: 'Tỷ lệ trễ', pct: true },
]

export const DEPARTMENT_METRICS: ReportMetric[] = [
  { key: 'orders', label: 'Số lần đặt' },
  { key: 'urgent', label: 'Số lần gấp' },
  { key: 'rate', label: 'Tỷ lệ gấp', pct: true },
]

export const SHIPPING_METRICS: ReportMetric[] = [
  { key: 'freq', label: 'Tần suất' },
  { key: 'order_value', label: 'Giá trị đơn hàng' },
  { key: 'ship_cost', label: 'Chi phí vận chuyển' },
  { key: 'rate', label: 'Tỷ lệ', pct: true },
]

/** Cột trạng thái YCMH — khớp enum thật trong DB, "Tổng" = tổng các cột sau. */
export const PYC_METRICS: ReportMetric[] = [
  { key: 'total', label: 'Tổng' },
  { key: 'draft', label: 'Nháp' },
  { key: 'submitted', label: 'Chờ duyệt' },
  { key: 'approved', label: 'Đã duyệt' },
  { key: 'dispatched', label: 'Đã điều phối' },
  { key: 'processing', label: 'Đang xử lý' },
  { key: 'completed', label: 'Hoàn tất' },
  { key: 'rejected', label: 'Từ chối' },
  { key: 'cancelled', label: 'Đã hủy' },
]

/** Cột trạng thái YCBG. */
export const YCKS_METRICS: ReportMetric[] = [
  { key: 'total', label: 'Tổng' },
  { key: 'draft', label: 'Nháp' },
  { key: 'submitted', label: 'Chờ duyệt' },
  { key: 'processing', label: 'Đang khảo sát' },
  { key: 'survey_done', label: 'Đã khảo sát' },
  { key: 'pr_created', label: 'Đã tạo yêu cầu mua hàng' },
  { key: 'done', label: 'Hoàn tất' },
  { key: 'cancelled', label: 'Đã hủy' },
]

/** Các form xuất Excel backend nhận (`_EXPORT_SHEETS`). */
export const EXPORT_SHEETS = [
  { sheet: 'all', label: 'Tất cả (5 báo cáo)' },
  { sheet: 'nspt', label: 'Nhân sự phụ trách' },
  { sheet: 'item_group', label: 'Phân loại VTBB/NL' },
  { sheet: 'supplier', label: 'Nhà cung cấp' },
  { sheet: 'department', label: 'Bộ phận (đơn gấp)' },
  { sheet: 'shipping', label: 'Chi phí vận chuyển' },
] as const

// ---- Khung dữ liệu trả về ----

/** Ma trận cả năm — một lần gọi trả đủ 5 chiều phân tích. */
export interface ReportMatrix {
  /** Thời điểm backend tính snapshot, hiện nguyên văn ở thanh mô tả kỳ. */
  computed_at: string
  year: string
  months: ReportMonth[]
  department: MatrixRow[]
  supplier: MatrixRow[]
  nspt: MatrixRow[]
  item_group: MatrixRow[]
  shipping: MatrixRow[]
}

/** Ma trận phòng ban × tháng của YCMH / YCBG. */
export interface RequestMatrix {
  months: ReportMonth[]
  rows: MatrixRow[]
}

export interface PayableBucket {
  total: number
  paid: number
  remaining: number
}

export interface DeliverySummary {
  on_time: number
  late: number
  total: number
}

export interface SpendPoint {
  month: string
  amount: number
}

/**
 * Số liệu tab Tổng quan.
 *
 * Endpoint `/api/reports/procurement` còn trả `by_supplier`, `by_nspt`,
 * `by_department`, `by_item_group`, `late_deliveries`, `inventory` — bản v1
 * KHÔNG hiện những phần đó (tab Tồn kho đã ẩn từ lâu) nên ở đây cũng không khai
 * báo. Cần dùng thì bổ sung, đừng đọc bằng `any`.
 */
export interface ProcurementReport {
  /** Đếm ĐMH theo trạng thái — giữ CẢ nháp/hủy để thấy phân bố. */
  po_status: Record<string, number>
  /** Số ĐMH THẬT (đã duyệt trở đi), không phải tổng của `po_status`. */
  po_count: number
  order_value: number
  payable_goods: PayableBucket
  payable_shipping: PayableBucket
  overdue: number
  inventory_value: number
  delivery: DeliverySummary
  /** Luôn trải cả năm, kể cả khi đang lọc phụ theo tháng. */
  spend_by_month: SpendPoint[]
}

export interface DailyRow {
  date: string
  day: string
  goods: number
  shipping: number
  amount: number
}

export interface DailyReport {
  month: string
  days: DailyRow[]
  total: number
}

export interface ShippingDetailRow {
  carrier: string
  month: string
  product_code: string
  misa_code: string
  invoice_no: string
  received_date: string
  qty_order: number
  qty_received: number
  order_amount: number
  ship_amount: number
  rate: number
}

export interface ShippingDetailResult {
  items: ShippingDetailRow[]
  total: number
  page: number
  page_size: number
  /** Danh sách đơn vị vận chuyển / tháng có phát sinh — dựng ô lọc từ đây. */
  carriers: string[]
  months: string[]
}

/** Một cột của biểu đồ chi phí theo tháng. */
export interface SpendBar {
  /** 'YYYY-MM' — dùng để gọi tiếp `/daily` khi bấm vào cột. */
  key: string
  label: string
  value: number
}

/**
 * Trải chi phí theo ĐỦ các tháng của kỳ, tháng chưa phát sinh để 0.
 *
 * Backend chỉ trả tháng có số; bỏ trống tháng rỗng thì trục thời gian bị co lại
 * và người đọc tưởng tháng đó không nằm trong kỳ.
 *
 * Nhãn cột rút còn "08" (`label` của backend là "08/2026"): 12 nhãn đầy đủ thì
 * recharts tự bỏ bớt nhãn cho khỏi chồng chữ — mất nhãn còn khó đọc hơn.
 */
export function spendSeries(months: ReportMonth[], spend: SpendPoint[]): SpendBar[] {
  const byMonth = new Map(spend.map((point) => [point.month, point.amount]))
  return months.map((month) => ({
    key: month.key,
    label: month.label.slice(0, 2),
    value: byMonth.get(month.key) ?? 0,
  }))
}
