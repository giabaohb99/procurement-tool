import { appRoutes } from '@/shared/constants/app-routes'

import { HolidayWorkReportFilters } from '../components/holiday-work-report-filters'
import type { ReportPageConfig } from '../types/report-analytics'
import { ReportAnalyticsPage } from './report-analytics-page'

const CONFIG: ReportPageConfig = {
  endpoint: '/api/holiday-work-report/summary',
  exportEndpoint: '/api/holiday-work-report/summary/export',
  drilldownEndpoint: '/api/holiday-work-report/summary/rows',
  entity: 'leave_comp_request',
  title: 'Làm việc vào ngày lễ, ngày nghỉ',
  description:
    'Ai đã đi làm vào ngày lễ hoặc ngày nghỉ theo lịch làm việc, bao nhiêu lượt, được duyệt bao nhiêu ngày nghỉ bù — theo phòng ban, nhân sự, loại ngày, tên ngày lễ. Không có chấm công: chỉ tính người đã lập phiếu nghỉ bù (mặc định chỉ phiếu đã duyệt). Kỳ tối đa 366 ngày.',
  slug: 'holiday-work',
  sourcePath: appRoutes.hr.leaveCompRequests,
  kpis: ['lines', 'people', 'holiday_lines', 'comp_days'],
  //  `pending_lines` chỉ có trong `meta` khi bật "Gồm phiếu chờ duyệt" — vắng thì bảng tự bỏ cột.
  tableMetrics: ['offday_lines', 'pending_lines'],
  chartMetric: 'lines',
  defaultGroupBy: 'department',
  defaultPreset: 'this_year',
  extraFilters: HolidayWorkReportFilters,
}

/**
 * Làm việc vào ngày lễ, ngày nghỉ (duoc-CR-717, khóa 30). Nguồn = phiếu nghỉ bù (D8a): mỗi phiếu là
 * một lượt đi làm ở `work_date`. Phòng ban lọc theo phòng GHI TRÊN PHIẾU. "Xem danh sách" chỉ có ở
 * chỉ số Lượt đi làm (`meta.drilldown_metrics`).
 */
export function HolidayWorkReportPage() {
  return <ReportAnalyticsPage config={CONFIG} />
}
