import type { ReportDrilldownTarget } from '../types/report-drilldown'

/**
 * Tham số `<gốc>/summary/rows` = MỌI tham số `/summary` đang xem (kỳ, so sánh, công ty,
 * phòng ban, lọc riêng của trang) + `metric` + nhóm.
 *
 * - Dòng Tổng / thẻ KPI → `group_by=none`, không `group_key`: đè hẳn `group_by` của trang,
 *   kẻo backend hiểu là "lọc nhóm" khi chỉ muốn cả danh sách.
 * - Dòng nhóm → `group_by` + `group_key` của nhóm đó; `group_key=""` là "(Chưa gắn)" và PHẢI
 *   được gửi (gửi thiếu = cả danh sách, đọc nhầm thành danh sách của nhóm chưa gắn).
 */
export function buildDrilldownParams(
  base: Record<string, string>,
  target: ReportDrilldownTarget,
): Record<string, string> {
  const params: Record<string, string> = { ...base, metric: target.metric }
  delete params.group_key
  if (target.group) {
    params.group_by = target.group.by
    params.group_key = target.group.key
  } else {
    params.group_by = 'none'
  }
  return params
}
