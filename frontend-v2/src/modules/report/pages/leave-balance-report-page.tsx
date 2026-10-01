import { appRoutes } from '@/shared/constants/app-routes'

import type { ReportPageConfig } from '../types/report-analytics'
import { ReportAnalyticsPage } from './report-analytics-page'

const CONFIG: ReportPageConfig = {
  endpoint: '/api/leave-balances/summary',
  exportEndpoint: '/api/leave-balances/summary/export',
  entity: 'leave_balance',
  title: 'Quỹ phép năm',
  description: 'Được cấp, đã dùng, đang giữ chỗ, còn lại và tỷ lệ sử dụng — theo loại nghỉ, công ty, phòng ban, nhân sự.',
  slug: 'leave-balance',
  sourcePath: appRoutes.hr.leaveBalances,
  kpis: ['granted', 'used', 'pending', 'remaining', 'usage_rate'],
  //  Kỳ của báo cáo này là NĂM, không có trục ngày/tuần/tháng bên trong một
  //  năm — backend luôn trả `trend: []`. `ReportTrendChart` tự nhận ra mảng
  //  rỗng và hiện khối "chưa có phát sinh" thay vì vẽ đường trống hay vỡ layout
  //  (xem `components/report-trend-chart.tsx`) — KHÔNG cần đổi khung dùng chung.
  chartMetric: 'granted',
  defaultGroupBy: 'leave_type',
  //  H2-FE (review 01/10/2026): kỳ của báo cáo này LÀ năm (xem docstring dưới) —
  //  mở trang lần đầu ở "Tháng này" (mặc định chung) rồi phải tự đổi sang "Năm
  //  nay" mới đúng ý nghĩa là một bước thừa. `compare` giữ mặc định `previous`:
  //  với preset lịch `this_year`, backend (`report_period._CALENDAR_UNIT_MONTHS`)
  //  tự lùi ĐÚNG 12 tháng — tức "cùng kỳ năm trước" — không cần khai thêm gì.
  defaultPreset: 'this_year',
  breakdowns: [{ key: 'leave_type', title: 'Top loại nghỉ' }],
}

/**
 * Báo cáo Quỹ phép năm (phase 04). Bộ lọc kỳ vẫn dùng chung bộ chọn Haravan
 * (preset/khoảng ngày) nhưng backend chỉ đọc NĂM của ngày kết thúc kỳ — chọn
 * "Năm nay"/"Năm trước"/một khoảng tùy ý trong năm đều cho cùng một kết quả
 * của năm đó; so sánh = năm liền trước (`notes` backend trả về giải thích rõ).
 * Phòng ban lấy theo hồ sơ HIỆN TẠI của nhân sự giữ quỹ (không có lịch sử
 * điều chuyển).
 */
export function LeaveBalanceReportPage() {
  return <ReportAnalyticsPage config={CONFIG} />
}
