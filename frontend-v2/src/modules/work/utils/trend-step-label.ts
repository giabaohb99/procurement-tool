/**
 * Bước thời gian của biểu đồ diễn biến (duoc-CR-782): kỳ dài hơn 31 ngày thì máy chủ gom theo TUẦN
 * (`overview_trend.DAILY_MAX_DAYS`), còn lại theo ngày. Dùng cho câu mô tả cạnh biểu đồ.
 */
export function trendStepLabel(periodDays: number): 'ngày' | 'tuần' {
  return periodDays > 31 ? 'tuần' : 'ngày'
}
