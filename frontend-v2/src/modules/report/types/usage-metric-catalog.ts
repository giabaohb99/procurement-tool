/** Hợp đồng JSON của `GET /api/usage-profiles/metrics` (duoc-CR-649): chỉ khóa và mã, chữ nằm ở lớp hiển thị. */
/** Một cột phân phối của tuần mới nhất: khoảng nửa mở `[lo, hi)`; cột tràn có `hi = null` (nghĩa «≥ lo»). */
export interface UsageMetricBucket {
  lo: number
  hi: number | null
  count: number
}

/** Trung vị công ty của một tuần snapshot; `median = null` khi tuần đó không ai đo được (duoc-CR-651). */
export interface UsageMetricTrendPoint {
  week: string
  median: number | null
  measured: number
}

export interface UsageMetricCatalogItem {
  key: string
  /** «3.1»…«3.6» — mục của backend. */
  section: string
  unit: string
  phase: number
  /** 1 càng cao càng tốt · -1 càng thấp càng tốt · 0 không phán xét. */
  direction: number
  measured_users: number
  total_users: number
  company_median: number | null
  /** `UnmeasuredReason` backend; null khi có người đo được hoặc chưa có snapshot. */
  unmeasured_reason: number | null
  /** Rỗng khi chưa ai đo được. */
  histogram: UsageMetricBucket[]
  /** Tối đa 8 tuần, tăng dần; tuần không có snapshot bị bỏ qua. */
  trend: UsageMetricTrendPoint[]
}

export interface UsageMetricCatalogResponse {
  week: string | null
  metrics: UsageMetricCatalogItem[]
  deferred: string[]
}
