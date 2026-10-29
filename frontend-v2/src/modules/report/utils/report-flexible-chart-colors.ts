import { CHART_COLORS, CHART_NEUTRAL } from '@/shared/ui/chart'

import type { FlexibleGroupItem } from './report-flexible-chart-series'

/**
 * Sáu màu cho tối đa sáu lát vành khuyên (`DONUT_MAX_GROUPS`). `index.css` mới khai BỐN tông
 * phân loại; lát 5, 6 dùng bậc nhạt của tông 1, 2 (pha với nền thẻ — vẫn đúng ở nền tối) thay
 * vì sinh thêm một sắc mới. Chú giải luôn ghi tên + số + %, nên màu không bao giờ là thứ duy
 * nhất phân biệt các lát.
 */
const DONUT_COLORS = [
  ...CHART_COLORS,
  'color-mix(in oklab, var(--chart-1) 45%, var(--card))',
  'color-mix(in oklab, var(--chart-2) 45%, var(--card))',
] as const

/** Màu MỘT màu cho mọi cột theo nhóm — độ dài đã nói độ lớn, tô theo giá trị là mã hóa hai lần. */
export const FLEXIBLE_CHART_BAR_COLOR = 'var(--chart-1)'

/** Màu lát theo VỊ TRÍ trong dãy đã xếp lớn → nhỏ; «Khác» luôn xám trung tính. */
export function pickDonutColor(item: FlexibleGroupItem, index: number): string {
  if (item.isRest) return CHART_NEUTRAL
  return DONUT_COLORS[index % DONUT_COLORS.length] ?? CHART_NEUTRAL
}
