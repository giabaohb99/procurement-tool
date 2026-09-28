import type { ReportMetricMeta } from '../types/report-analytics'

/**
 * Cột nào lên bảng "Xem theo" và THỨ TỰ của chúng — dùng chung một luật với
 * thẻ KPI: chỉ số `helper` (mẫu số phụ của một `derived`, backend đánh dấu
 * `helper: true`) KHÔNG BAO GIỜ hiện. Trong các chỉ số còn lại, những khóa nằm
 * trong `kpis` (`ReportPageConfig.kpis`, đã sắp theo ý người cấu hình trang)
 * đứng TRƯỚC, đúng thứ tự đó; chỉ số nào không nằm trong `kpis` xếp tiếp theo,
 * giữ nguyên thứ tự backend trả về trong `meta.metrics`.
 */
export function orderVisibleReportMetrics(
  metrics: ReportMetricMeta[],
  kpis: string[],
): ReportMetricMeta[] {
  const visible = metrics.filter((m) => !m.helper)
  const byKey = new Map(visible.map((m) => [m.key, m]))

  const ordered: ReportMetricMeta[] = []
  for (const key of kpis) {
    const metric = byKey.get(key)
    if (metric) {
      ordered.push(metric)
      byKey.delete(key)
    }
  }
  //  `Map` giữ đúng thứ tự chèn — các chỉ số còn lại (chưa bị xóa ở trên) vẫn
  //  đứng theo thứ tự gốc của `visible`.
  ordered.push(...byKey.values())

  return ordered
}
