import { appRoutes } from '@/shared/constants/app-routes'

import type { ReportPageConfig } from '../types/report-analytics'
import { ReportAnalyticsPage } from './report-analytics-page'

const CONFIG: ReportPageConfig = {
  endpoint: '/api/employees/summary',
  exportEndpoint: '/api/employees/summary/export',
  entity: 'employee',
  title: 'Biến động nhân sự',
  description:
    'Định biên đầu/cuối kỳ, vào mới, nghỉ việc, tỷ lệ nghỉ việc — xem theo phòng ban, cấp bậc, loại hình, giới tính, chức vụ, thâm niên.',
  slug: 'hr-headcount',
  sourcePath: appRoutes.hr.employees,
  //  `headcount_end` là chỉ số THỜI ĐIỂM (snapshot) — vẫn hiện thẻ KPI (không
  //  sparkline, không bấm đổi biểu đồ), cùng khuôn `debt_overdue` của Báo cáo
  //  mua hàng. `new_hires`/`departures` là chỉ số CỘNG ĐƯỢC, có xu hướng.
  kpis: ['headcount_end', 'new_hires', 'departures', 'turnover_rate'],
  chartMetric: 'new_hires',
  defaultGroupBy: 'department',
  breakdowns: [{ key: 'status', title: 'Theo trạng thái' }],
}

/**
 * Báo cáo Nhân sự — biến động & cơ cấu (phase 04). Phòng ban/cấp bậc/chức
 * vụ/loại hình lấy theo hồ sơ HIỆN TẠI (không có lịch sử điều chuyển — xem
 * `notes` backend trả về); "Định biên cuối kỳ" chỉ hiện ở thẻ KPI Tổng, không
 * có đường xu hướng riêng (số TẠI MỘT THỜI ĐIỂM, không cộng dồn theo mốc).
 */
export function HrHeadcountReportPage() {
  return <ReportAnalyticsPage config={CONFIG} />
}
