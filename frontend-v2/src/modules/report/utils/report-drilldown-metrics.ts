import type { ReportMeta } from '../types/report-analytics'

export interface ReportDrilldownMetricOption {
  key: string
  label: string
}

/**
 * Chỉ số mở được danh sách = `meta.drilldown_metrics` ∩ `meta.metrics`, giữ thứ tự backend
 * gửi. Khóa có trong `drilldown_metrics` mà KHÔNG có trong `metrics` (vd nhóm nhạy cảm bị
 * backend gỡ vì người xem thiếu quyền) bị bỏ — không có nhãn thật thì không mời bấm.
 */
export function listDrilldownMetrics(meta: ReportMeta): ReportDrilldownMetricOption[] {
  const byKey = new Map(meta.metrics.map((m) => [m.key, m.label]))
  const seen = new Set<string>()
  const out: ReportDrilldownMetricOption[] = []
  for (const key of meta.drilldown_metrics ?? []) {
    const label = byKey.get(key)
    if (label === undefined || seen.has(key)) continue
    seen.add(key)
    out.push({ key, label })
  }
  return out
}

/**
 * Chỉ số mặc định khi mở danh sách từ một DÒNG nhóm (không bấm vào chỉ số cụ thể nào):
 * khóa đầu tiên trong `preferred` (chỉ số đang vẽ biểu đồ, rồi tới thứ tự thẻ KPI) có
 * danh sách, không có thì chỉ số đầu của backend. Không chỉ số nào → `null`.
 */
export function pickDefaultDrilldownMetric(
  options: ReportDrilldownMetricOption[],
  preferred: string[],
): string | null {
  const keys = new Set(options.map((o) => o.key))
  return preferred.find((k) => keys.has(k)) ?? options[0]?.key ?? null
}

/**
 * Chỉ số mở sẵn khi bấm "Xem" ở MỘT dòng nhóm: ưu tiên như `pickDefaultDrilldownMetric`
 * (chỉ số biểu đồ, rồi thẻ KPI) nhưng chỉ nhận chỉ số mà dòng đó có giá trị > 0 — nếu không,
 * ngăn mở ra "0 dòng" dù dòng đang ghi 103 người. Thử cả phần còn lại của `options` theo thứ tự
 * backend; dòng không chỉ số nào > 0 thì lùi về mặc định.
 */
export function pickDrilldownMetricForRow(
  options: ReportDrilldownMetricOption[],
  preferred: string[],
  values: Record<string, number | null | undefined>,
): string | null {
  const keys = new Set(options.map((o) => o.key))
  const candidates = [...preferred.filter((k) => keys.has(k)), ...options.map((o) => o.key)]
  const positive = candidates.find((k) => (values[k] ?? 0) > 0)
  return positive ?? pickDefaultDrilldownMetric(options, preferred)
}
