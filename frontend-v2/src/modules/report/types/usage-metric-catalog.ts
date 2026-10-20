/** Hợp đồng JSON của `GET /api/usage-profiles/metrics` (duoc-CR-644): chỉ khóa và mã, chữ nằm ở lớp hiển thị. */
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
}

export interface UsageMetricCatalogResponse {
  week: string | null
  metrics: UsageMetricCatalogItem[]
  deferred: string[]
}
