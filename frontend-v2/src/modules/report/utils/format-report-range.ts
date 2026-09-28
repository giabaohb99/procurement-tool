import { formatDate } from '@/shared/utils/format-date'

/**
 * Khoảng ngày của một kỳ báo cáo: "01/09/2026 – 28/09/2026", còn kỳ MỘT ngày
 * (Hôm nay / Hôm qua) chỉ in một ngày — "28/09/2026 – 28/09/2026" đọc như lỗi.
 */
export function formatReportRange(from: string, to: string): string {
  if (!from) return ''
  if (!to || from === to) return formatDate(from)
  return `${formatDate(from)} – ${formatDate(to)}`
}
