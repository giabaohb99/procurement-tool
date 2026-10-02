/**
 * Số cột của lưới thẻ KPI theo SỐ THẺ — lưới cứng 4 cột làm báo cáo 5 thẻ xếp
 * thành 4 + 1, thẻ thứ năm đứng lẻ loi một hàng (người dùng chê 28/09/2026).
 * 5 thẻ → 5 cột; 6 thẻ → 3 cột (hai hàng đều); còn lại tối đa 4 cột.
 */
export function kpiGridColumnsClass(count: number): string {
  if (count === 5) return 'xl:grid-cols-5'
  if (count === 6) return 'xl:grid-cols-3'
  if (count === 3) return 'xl:grid-cols-3'
  return 'xl:grid-cols-4'
}
