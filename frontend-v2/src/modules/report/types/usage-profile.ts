/**
 * Hợp đồng JSON của `/api/usage-profiles` (duoc-CR-641, phase 05). Mọi trường
 * ngoài định danh đều TÙY CHỌN/nullable: backend thêm chỉ số theo từng đợt và
 * một chỉ số chưa đo được thì KHÔNG có giá trị (khác 0) — xem `unmeasured`.
 */

/** Chỉ số một người: giá trị `v`, trung vị nhóm `med`, 4 giá trị tuần gần nhất `trend`. */
export interface UsageMetricValue {
  v: number | null
  med?: number | null
  /** Phân vị 75 của nhóm so sánh. */
  p75?: number | null
  trend?: (number | null)[]
}

/** Mã lý do chưa đo được — `UnmeasuredReason` backend: 1 chưa thu · 2 dưới ngưỡng · 3 không áp dụng. */
export type UsageUnmeasured = Record<string, number>

export interface UsageLabel {
  /** `UsageStyle` backend (1..10). */
  code: number
  score: number
  /** Khóa chỉ số đã kích hoạt điều kiện gắn nhãn. */
  evidence: string[]
}

/** Số lần theo động từ: c lập · u sửa · s gửi · a duyệt · r từ chối · t trả về · d xóa. */
export interface UsageDocCounts {
  c?: number
  u?: number
  s?: number
  a?: number
  r?: number
  t?: number
  d?: number
}

/** `screens_source` backend: 1 sự kiện giao diện · 2 ước lượng từ nhật ký API. */
export type UsageScreensSource = 1 | 2

/** Danh sách đã gom của snapshot tuần; mọi khóa tùy chọn (chỉ số chưa đo thì thiếu). */
export interface UsageSnapshotLists {
  /** 7 hàng (thứ Hai đầu) × 24 cột giờ VN. */
  heatmap?: number[][]
  /** [route, lượt xem, thời gian ở lại ms, số lời gọi API] */
  top_screens?: [string, number, number, number][]
  screens_source?: UsageScreensSource
  /** [route, thời gian ở lại ms] */
  module_time?: [string, number][]
  /** [route hay mở đầu ngày, số ngày, số lần đổi]; rỗng khi chưa có. */
  first_screen?: [string, number, number] | []
  top_paths?: [string, string, string, number][]
  /** [mã báo cáo `ReportKey`, số lần xem] */
  reports?: [number, number][]
  /** [route, số lần bị 403] */
  top_403_routes?: [string, number][]
  docs?: Record<string, UsageDocCounts>
  /** Nhóm 3.8: {mã kênh `AI_CHANNEL`: số lượt}. */
  ai_channels?: Record<string, number>
  /** Nhóm 3.8: {mã ứng dụng `AI_CLIENT`: số lượt} — chỉ kênh ứng dụng AI ngoài. */
  ai_clients?: Record<string, number>
  /** Nhóm 3.8: [mã nhóm công cụ, số lượt]. */
  ai_tool_groups?: [string, number][]
}

export interface UsageCohort {
  kind: number
  key: number
  size: number
  name: string
}

export interface UsageSnapshot {
  period?: { start: string; end: string; window_weeks: number }
  context?: {
    workdays_net?: number | null
    leave_days?: number | null
    holidays?: number | null
    on_behalf_received?: number | null
    /** Ngày bắt đầu có sự kiện giao diện. */
    tracking_since?: string | null
  }
  /** Nhóm so sánh: `kind` = `CohortKind` (1 vai trò · 2 pháp nhân · 3 toàn công ty). */
  cohort?: UsageCohort
  metrics: Record<string, UsageMetricValue>
  schema_version?: number
  period_start?: string
  counts?: Record<string, number>
  lists?: UsageSnapshotLists
  unmeasured?: UsageUnmeasured
  labels?: UsageLabel[]
}

export interface UsageDailyRow {
  day: string
  active: boolean
  is_workday: boolean
  is_holiday?: boolean
  work_capacity?: number
  leave_days?: number
  first_seen_min?: number | null
  last_action_min?: number | null
  work_bursts?: number
  active_minutes?: number
  api_reads?: number
  api_writes?: number
  writes_offhours?: number
  approvals?: number
  exports?: number
  http_403?: number
  http_422?: number
  page_views?: number
  on_behalf_received?: number
}

export interface UsageScreen {
  /** Route MẪU, không chứa id (`/procurement/purchase-orders/:id`). */
  route: string
  views: number
  dwell_ms: number
  api_calls: number
}

/** Một chỉ số trong `metric_meta` (không có nhãn — FE giữ nhãn tiếng Việt riêng). */
export interface UsageMetricMeta {
  unit: string
  section: string
  phase: number
  direction: string
}

/** Một snapshot tuần trong chuỗi `weekly` (tăng dần theo `period_start`). */
export interface UsageWeeklyPoint {
  period_start: string
  cohort_size: number
  metrics: Record<string, number>
  labels: number[]
}

export interface UsageProfileDetail {
  subject: {
    user_id: number
    full_name: string
    emp_code?: string | null
    position?: string | null
    department_name?: string | null
    company_name?: string | null
    role_names: string[]
    hire_date?: string | null
    tenure_days?: number | null
  }
  latest: UsageSnapshot | null
  weekly: UsageWeeklyPoint[]
  daily: UsageDailyRow[]
  /** 7 hàng (thứ Hai đầu) × 24 cột (giờ VN). */
  heatmap: number[][]
  /** Tối đa 20 màn; nguồn số liệu nằm ở `screens_source` (một giá trị cho cả danh sách). */
  screens: UsageScreen[]
  screens_source: UsageScreensSource
  metric_meta: Record<string, UsageMetricMeta>
  /** Chỉ số hoãn/bỏ theo định nghĩa — không bao giờ có giá trị. */
  deferred_metrics: string[]
  data_since: string | null
  tracking_since: string | null
}

export interface UsageProfileRow {
  user_id: number
  full_name: string
  emp_code?: string | null
  department_name?: string | null
  company_name?: string | null
  /** Nhóm so sánh của snapshot tuần mới nhất; null khi chưa có snapshot. */
  cohort: UsageCohort | null
  active_days: number
  workdays_net: number
  active_ratio: number | null
  api_writes: number
  docs_created: number
  approvals: number
  exports: number
  http_422_per_100_writes: number | null
  labels: { code: number; score: number }[]
  last_active_day: string | null
  /** duoc-CR-650: chỉ có khi gọi kèm `metric`; null = chưa đo được (KHÁC 0). */
  metric_value?: number | null
}

export interface UsageProfileListResponse {
  items: UsageProfileRow[]
  total: number
  page: number
  page_size: number
  /** Tuần (thứ Hai) của snapshot lấy nhãn/nhóm. */
  label_week: string | null
  period: { date_from: string; date_to: string }
  /** Ngày sớm nhất có số liệu gom. */
  data_since: string | null
}
