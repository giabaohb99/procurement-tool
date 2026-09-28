import type { ComponentType } from 'react'

import type { PermissionEntity } from '@/core/authorization/permission-types'

/**
 * Hợp đồng JSON chuẩn của MỌI đường `/summary` báo cáo kiểu Haravan — khớp
 * `backend/app/core/report_aggregate.py` (phase-01 §Architecture). Một khung
 * chung cho mọi phân hệ: backend là nguồn DUY NHẤT của nhãn chỉ số/chiều, kỳ so
 * sánh và độ hạt thời gian — tầng này KHÔNG được gõ tay danh sách trạng thái.
 */

/** Đơn vị của một chỉ số — quyết định cách định dạng số (`format-report-metric.ts`). */
export type ReportMetricKind = 'int' | 'money' | 'days' | 'hours' | 'percent'

/** Chiều nào là TỐT khi chỉ số tăng. `null` = trung tính, không tô màu ±%. */
export type ReportMetricGoodDirection = 'up' | 'down' | null

export interface ReportMetricMeta {
  key: string
  label: string
  kind: ReportMetricKind
  good: ReportMetricGoodDirection
  /**
   * Chỉ số PHỤ (vd mẫu số của một `derived`) — backend vẫn trả nó trong
   * `meta.metrics` để tính, nhưng nó KHÔNG được hiện ở bất kỳ đâu: thẻ KPI,
   * ô chọn chỉ số biểu đồ, cột bảng "Xem theo", sparkline. Thay cho
   * `ReportPageConfig.hiddenMetrics` cũ (đã bỏ) — backend là nguồn DUY NHẤT.
   */
  helper: boolean
  /**
   * Chỉ số "số dư hiện tại" (vd `debt_remaining`/`debt_overdue`) — chỉ có giá
   * trị Ở TỔNG (`totals`), KHÔNG có mặt trong `trend[]`/`groups[]` (cộng dồn
   * theo kỳ không có nghĩa với một số dư tại-một-thời-điểm). Hiện thành thẻ
   * KPI KHÔNG sparkline, KHÔNG bấm đổi biểu đồ xu hướng; ở bảng "Xem theo" chỉ
   * hiện trên dòng Tổng, các dòng nhóm hiện "—".
   */
  snapshot: boolean
}

export interface ReportDimensionMeta {
  key: string
  label: string
}

export interface ReportMeta {
  metrics: ReportMetricMeta[]
  dimensions: ReportDimensionMeta[]
  /** Chiều đang "Xem theo" — bằng `group_by` đã gửi lên. */
  group_by: string
  /** Chỉ số xếp hạng nhóm + giá trị của các khối "Top" (breakdowns). */
  rank_by?: string | null
}

export type ReportCompareMode = 'previous' | 'year' | 'none'

export interface ReportPeriod {
  date_from: string
  date_to: string
  /** `null` khi `compare=none` hoặc kỳ so sánh không xác định được. */
  compare_from: string | null
  compare_to: string | null
  compare: ReportCompareMode
  granularity: 'day' | 'week' | 'month'
  /** Khóa preset backend đã áp — phản chiếu đúng tham số `preset` đã gửi lên. */
  preset: string
}

/**
 * Giá trị các chỉ số tại MỘT mốc/nhóm — khóa theo `meta.metrics[].key`.
 * `null` = chỉ số DẪN XUẤT với mẫu số 0 ("chưa có gì để đo", KHÁC số 0 thật —
 * hiện "—", không hiện "0%"). Khóa VẮNG MẶT (không phải `null`) = chỉ số
 * `snapshot` ở một mốc/nhóm không áp dụng (xem `ReportMetricMeta.snapshot`).
 */
export type ReportMetricValues = Record<string, number | null>

export interface ReportTrendPoint {
  key: string
  label: string
  current: ReportMetricValues
  /** `null` = mốc này kỳ so sánh không có (thiếu mốc, hoặc `compare=none`). */
  compare: ReportMetricValues | null
}

export interface ReportGroupRow {
  key: string
  label: string
  current: ReportMetricValues
  compare: ReportMetricValues | null
}

export interface ReportBreakdownItem {
  key: string
  label: string
  value: number
}

export interface ReportAnalyticsResponse {
  period: ReportPeriod
  meta: ReportMeta
  totals: {
    current: ReportMetricValues
    compare: ReportMetricValues | null
  }
  trend: ReportTrendPoint[]
  /** Bỏ trống khi gọi với `group_by=none` (trang Tổng quan gọi nhẹ). */
  groups?: ReportGroupRow[]
  breakdowns?: Record<string, ReportBreakdownItem[]>
  notes?: string[]
}

/** Một breakdown phụ hiện thành biểu đồ cột ngang "Top" dưới biểu đồ xu hướng. */
export interface ReportBreakdownConfig {
  /** Khóa trong `response.breakdowns`. */
  key: string
  title: string
}

/**
 * Props mà component lọc riêng của trang (`ReportPageConfig.extraFilters`)
 * nhận được. Rỗng vì trạng thái lọc nằm THẲNG trên URL — component tự đọc/ghi
 * bằng `useUrlParamState` như mọi ô lọc khác trong hệ (xem `docs/ui/table.md`),
 * `ReportAnalyticsPage` gom lại qua `queryParams` của `useReportFilters` mà
 * không cần biết tên tham số riêng đó là gì.
 */
export type ReportExtraFiltersProps = Record<string, never>

/**
 * Cấu hình MỘT trang báo cáo — mỗi báo cáo mới chỉ cần khai một bản này rồi
 * truyền cho `ReportAnalyticsPage`. Toàn bộ giao diện (bộ lọc kỳ, thẻ KPI, biểu
 * đồ xu hướng, bảng nhóm) dựng từ `meta` + dữ liệu backend trả về.
 */
export interface ReportPageConfig {
  /** Đường `/summary`, vd `/api/reports/pr-lines/summary`. */
  endpoint: string
  /** Đường xuất Excel (cùng bộ lọc, `require(entity,'export')`). Bỏ trống = ẩn nút Xuất Excel. */
  exportEndpoint?: string
  /** Khóa quyền gác nút Xuất Excel — `can(entity, 'export')`. */
  entity: PermissionEntity
  title: string
  description: string
  /**
   * Khóa NGẮN, duy nhất trong toàn hệ — dùng làm `storageKey="report.<slug>"`
   * của bảng nhóm và tên tệp xuất Excel (`bao-cao-<slug>-<from>-<to>.xlsx`).
   */
  slug: string
  /** Trang BẢNG gốc — nút "Xem bảng chi tiết". Bỏ trống = ẩn nút (nguồn không phải bảng). */
  sourcePath?: string
  /** Khóa chỉ số hiện thành thẻ KPI, ĐÚNG THỨ TỰ trái sang phải. */
  kpis: string[]
  /** Chỉ số mặc định vẽ trên biểu đồ xu hướng — bấm thẻ KPI khác để đổi. */
  chartMetric: string
  /** `group_by` mặc định khi mở trang lần đầu — phải khớp một khóa `meta.dimensions` backend trả. */
  defaultGroupBy: string
  /** Breakdown phụ (Top NCC, Top NSTM…) — chỉ vẽ khi backend có trả đúng khóa trong `breakdowns`. */
  breakdowns?: ReportBreakdownConfig[]
  /** Ô lọc riêng của trang, chèn vào thanh lọc TRƯỚC ô Công ty. */
  extraFilters?: ComponentType<ReportExtraFiltersProps>
  /** Nguồn không lọc theo công ty (vd Báo cáo khảo sát) — ẩn ô Công ty. */
  hideCompany?: boolean
}
