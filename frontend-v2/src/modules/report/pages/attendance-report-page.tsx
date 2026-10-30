import { appRoutes } from '@/shared/constants/app-routes'

import { ReportDepartmentFilter } from '../components/report-department-filter'
import type { ReportPageConfig } from '../types/report-analytics'
import { ReportAnalyticsPage } from './report-analytics-page'

const CONFIG: ReportPageConfig = {
  endpoint: '/api/attendance-report/summary',
  exportEndpoint: '/api/attendance-report/summary/export',
  drilldownEndpoint: '/api/attendance-report/summary/rows',
  entity: 'employee',
  title: 'Có mặt theo ngày',
  description:
    'Mỗi ngày trong kỳ × mỗi người đang làm: số người-ngày phải làm theo lịch làm việc (trừ ngày lễ), người-ngày nghỉ theo đơn đã duyệt (nửa buổi tính 0,5) và người-ngày có mặt. Kỳ tối đa 92 ngày. Không phải chấm công — số có mặt suy từ lịch và đơn nghỉ.',
  slug: 'attendance',
  //  "Xem lịch" (ai làm, ai nghỉ) gác `employee.read` — đúng khóa của báo cáo này.
  sourcePath: appRoutes.hr.workRoster,
  kpis: ['scheduled', 'present', 'on_leave', 'present_rate'],
  tableMetrics: ['absence_rate'],
  chartMetric: 'present_rate',
  defaultGroupBy: 'department',
  defaultPreset: 'this_month',
  extraFilters: ReportDepartmentFilter,
}

/**
 * Có mặt theo ngày (C3, duoc-CR-689, khóa 26). Thiếu quyền xem đơn nghỉ thì chỉ số nghỉ để
 * trống (backend ghi chú ở `notes`) và "Xem danh sách" người nghỉ trả 403 — thẻ lỗi của ngăn.
 */
export function AttendanceReportPage() {
  return <ReportAnalyticsPage config={CONFIG} />
}
