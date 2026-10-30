import { formatRatio } from './usage-format'

export const NOT_ENOUGH_SAMPLES = 'chưa đủ mẫu'
const NONE = '—'

/** Số ngày (đã làm tròn 2 số lẻ ở backend) → "3,5 ngày". `null` = không có số (khác với 0 ngày). */
export function formatDays(days: number | null | undefined): string {
  if (days == null || !Number.isFinite(days)) return NONE
  return `${Number.isInteger(days) ? days : days.toFixed(1).replace('.', ',')} ngày`
}

/** Số lần làm lại trên mỗi phiếu, 0..n — hiện phần trăm cho dễ đọc ("8%"). */
export function formatRework(rate: number | null | undefined): string {
  return formatRatio(rate)
}

/** Giờ thực tế / giờ ước lượng → "1,5×". */
export function formatEstimateRatio(ratio: number | null | undefined): string {
  if (ratio == null || !Number.isFinite(ratio)) return NONE
  return `${ratio.toFixed(2).replace(/\.?0+$/, '').replace('.', ',')}×`
}

/** Tên hiển thị của một dòng: loại phiếu, kèm loại việc nếu là việc Dự án. */
export function typeLabel(row: { kind_label: string; task_type_name: string }): string {
  return row.task_type_name ? `${row.kind_label} › ${row.task_type_name}` : row.kind_label
}
