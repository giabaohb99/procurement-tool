import type { ReportMeta } from '../types/report-analytics'
import { formatReportMetricValue } from './format-report-metric'

/**
 * Các khối "Top" (breakdown) xếp theo chỉ số `meta.rank_by` do backend chọn —
 * vd Top NCC theo GIÁ TRỊ ĐẶT HÀNG chứ không theo số dòng. Hàm này trả câu mô
 * tả ("Theo Giá trị đặt hàng") và hàm định dạng số ở đầu cột theo đúng `kind`
 * của chỉ số đó, để tiền hiện "1,2 tỷ đ" chứ không ra một con số trần.
 */
export function describeBreakdownRank(meta?: ReportMeta): {
  description?: string
  formatValue?: (value: number) => string
} {
  const metric = meta?.metrics.find((m) => m.key === meta.rank_by)
  if (!metric) return {}
  return {
    description: `Theo ${metric.label.toLocaleLowerCase('vi-VN')}`,
    formatValue: (value) => formatReportMetricValue(value, metric.kind, 'compact'),
  }
}
