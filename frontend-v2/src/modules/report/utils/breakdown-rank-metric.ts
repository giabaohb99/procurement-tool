import type { ReportMeta } from '../types/report-analytics'
import { formatReportMetricValue } from './format-report-metric'

/**
 * Các khối "Top" (breakdown) xếp theo chỉ số `meta.rank_by` do backend chọn —
 * vd Top NCC theo GIÁ TRỊ ĐẶT HÀNG chứ không theo số dòng. Hàm này trả câu mô
 * tả ("Theo Giá trị đặt hàng") và hàm định dạng số ở đầu cột theo đúng `kind`
 * của chỉ số đó, để tiền hiện "1,2 tỷ đ" chứ không ra một con số trần.
 *
 * `rankMetric` (review H3, 01/10/2026): ghi đè `meta.rank_by` cho ĐÚNG MỘT
 * breakdown — trang có nhiều khối "Top" xếp theo nhiều chỉ số khác nhau (vd
 * `work-report-page.tsx`: "Top dự án theo quá hạn" / "Top PIC theo việc mở",
 * hai chỉ số snapshot khác nhau) thì không thể dùng chung MỘT `meta.rank_by`
 * cho mọi khối — khai `ReportBreakdownConfig.rankMetric` ở đúng khối cần.
 */
export function describeBreakdownRank(
  meta?: ReportMeta,
  rankMetric?: string,
): {
  description?: string
  formatValue?: (value: number) => string
} {
  const key = rankMetric ?? meta?.rank_by
  const metric = meta?.metrics.find((m) => m.key === key)
  if (!metric) return {}
  return {
    description: `Theo ${metric.label.toLocaleLowerCase('vi-VN')}`,
    formatValue: (value) => formatReportMetricValue(value, metric.kind, 'compact'),
  }
}
