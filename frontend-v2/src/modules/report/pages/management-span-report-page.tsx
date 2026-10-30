import { appRoutes } from '@/shared/constants/app-routes'

import { ReportDepartmentFilter } from '../components/report-department-filter'
import type { ReportPageConfig } from '../types/report-analytics'
import { ReportAnalyticsPage } from './report-analytics-page'

const CONFIG: ReportPageConfig = {
  endpoint: '/api/management-span/summary',
  exportEndpoint: '/api/management-span/summary/export',
  drilldownEndpoint: '/api/management-span/summary/rows',
  entity: 'employee',
  title: 'Cơ cấu quản lý',
  description:
    'Ai đang quản lý ai tại cuối kỳ: số quản lý, số cấp dưới bình quân, người chưa gán quản lý trực tiếp, quản lý chỉ 1 hoặc trên 10 cấp dưới, người nghỉ việc dưới quyền từng quản lý.',
  slug: 'management-span',
  sourcePath: appRoutes.hr.employees,
  kpis: ['managers', 'avg_span', 'unassigned_manager', 'span_wide'],
  tableMetrics: ['staff', 'span_one', 'departures_under'],
  //  Bắt buộc theo kiểu, nhưng không dùng: `hideTrend` (backend luôn trả `trend: []`).
  chartMetric: 'managers',
  defaultGroupBy: 'department',
  extraFilters: ReportDepartmentFilter,
  hideTrend: true,
}

/**
 * Cơ cấu quản lý (A3, duoc-CR-688, khóa 23). Số tại mốc `min(cuối kỳ, hôm nay)` theo ô
 * "Quản lý trực tiếp" của hồ sơ; "Xem theo Quản lý" cho mỗi quản lý một dòng.
 */
export function ManagementSpanReportPage() {
  return <ReportAnalyticsPage config={CONFIG} />
}
