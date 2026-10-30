import { appRoutes } from '@/shared/constants/app-routes'

import { ReportDepartmentFilter } from '../components/report-department-filter'
import type { ReportPageConfig } from '../types/report-analytics'
import { ReportAnalyticsPage } from './report-analytics-page'

const CONFIG: ReportPageConfig = {
  endpoint: '/api/work-moves/summary',
  exportEndpoint: '/api/work-moves/summary/export',
  drilldownEndpoint: '/api/work-moves/summary/rows',
  entity: 'employee',
  title: 'Điều chuyển & bổ nhiệm',
  description:
    'Điều chuyển, bổ nhiệm, kiêm nhiệm, miễn nhiệm trong kỳ theo quá trình công tác; số người có biến động, thời gian từ lúc vào làm tới lần bổ nhiệm, kiêm nhiệm đang hiệu lực và sắp hết.',
  slug: 'work-moves',
  sourcePath: appRoutes.hr.employees,
  kpis: ['transfers', 'appoints', 'people_moved', 'concurrent_active'],
  chartMetric: 'transfers',
  defaultGroupBy: 'event_type',
  extraFilters: ReportDepartmentFilter,
}

/**
 * Điều chuyển & bổ nhiệm (D1, duoc-CR-688, khóa 24). Hàng = dòng quá trình công tác có
 * "Từ ngày" trong kỳ (đã áp hay chưa áp đều tính — xem `notes`). "Xem theo Phòng đi → Phòng
 * đến" cho thấy dòng người chảy giữa các phòng.
 */
export function WorkMovesReportPage() {
  return <ReportAnalyticsPage config={CONFIG} />
}
