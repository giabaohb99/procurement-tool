import { appRoutes } from '@/shared/constants/app-routes'

import { LeaveBalanceExtraFilters } from '../components/leave-balance-extra-filters'
import type { ReportPageConfig } from '../types/report-analytics'
import { ReportAnalyticsPage } from './report-analytics-page'

const CONFIG: ReportPageConfig = {
  endpoint: '/api/leave-balances/summary',
  exportEndpoint: '/api/leave-balances/summary/export',
  drilldownEndpoint: '/api/leave-balances/summary/rows',
  entity: 'leave_balance',
  title: 'Quỹ phép năm',
  description: 'Được cấp, đã dùng, đang giữ chỗ, còn lại và tỷ lệ sử dụng — theo loại nghỉ, công ty, phòng ban, nhân sự.',
  slug: 'leave-balance',
  sourcePath: appRoutes.hr.leaveBalances,
  //  `people_missing_balance` ("Chưa được cấp quỹ", duoc-CR-686) là chỉ số THỜI ĐIỂM — chỉ ở Tổng.
  kpis: ['granted', 'used', 'pending', 'remaining', 'usage_rate', 'people_missing_balance'],
  //  Kỳ của báo cáo này là NĂM, không có trục ngày/tuần/tháng bên trong một
  //  năm — backend luôn trả `trend: []`, nên ẩn hẳn khung biểu đồ (duoc-CR-686)
  //  thay vì để một khối "chưa có phát sinh" trống trơn.
  chartMetric: 'granted',
  hideTrend: true,
  defaultGroupBy: 'leave_type',
  //  H2-FE (review 01/10/2026): kỳ của báo cáo này LÀ năm (xem docstring dưới) —
  //  mở trang lần đầu ở "Tháng này" (mặc định chung) rồi phải tự đổi sang "Năm
  //  nay" mới đúng ý nghĩa là một bước thừa. `compare` giữ mặc định `previous`:
  //  với preset lịch `this_year`, backend (`report_period._CALENDAR_UNIT_MONTHS`)
  //  tự lùi ĐÚNG 12 tháng — tức "cùng kỳ năm trước" — không cần khai thêm gì.
  defaultPreset: 'this_year',
  breakdowns: [{ key: 'leave_type', title: 'Top loại nghỉ' }],
  //  Phòng ban (hiện tại của người giữ quỹ) + trạng thái nhân sự (mặc định "Đang làm").
  extraFilters: LeaveBalanceExtraFilters,
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
