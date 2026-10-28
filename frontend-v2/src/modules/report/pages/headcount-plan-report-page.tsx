import { appRoutes } from '@/shared/constants/app-routes'

import { ReportDepartmentFilter } from '../components/report-department-filter'
import type { ReportPageConfig } from '../types/report-analytics'
import { ReportAnalyticsPage } from './report-analytics-page'

const CONFIG: ReportPageConfig = {
  endpoint: '/api/headcount-plan-report/summary',
  exportEndpoint: '/api/headcount-plan-report/summary/export',
  drilldownEndpoint: '/api/headcount-plan-report/summary/rows',
  entity: 'headcount_plan',
  title: 'Số người kế hoạch so với thực tế',
  description:
    'Số người theo Kế hoạch nhân sự có hiệu lực ở tháng cuối kỳ (kế hoạch tháng, quý, bán niên được ưu tiên hơn kế hoạch năm) so với số người đang làm tại cuối kỳ: còn thiếu, vượt, tỷ lệ lấp đầy. Dòng «Toàn pháp nhân» so với tổng người của pháp nhân, không cộng dồn với các dòng phòng; phòng có người mà chưa có kế hoạch hiện «chưa có kế hoạch».',
  slug: 'headcount-plan',
  sourcePath: appRoutes.hr.headcountPlans,
  kpis: ['planned', 'actual', 'vacancies', 'fill_rate'],
  //  «Đang làm ở phòng chưa có kế hoạch» — người đang có mà không phòng nào lập kế hoạch cho.
  tableMetrics: ['gap', 'over', 'unplanned'],
  //  Bắt buộc theo kiểu, nhưng không dùng cho xu hướng: `hideTrend` (số tại một mốc).
  chartMetric: 'vacancies',
  //  Kế hoạch lập theo pháp nhân — mặc định xem theo công ty.
  defaultGroupBy: 'company',
  //  Kế hoạch là kế hoạch NĂM — mở trang là thấy cả năm nay.
  defaultPreset: 'this_year',
  extraFilters: ReportDepartmentFilter,
  hideTrend: true,
}

/**
 * Số người kế hoạch so với thực tế (A4, duoc-CR-689, khóa 25). Nguồn kế hoạch là màn
 * Nhân sự ▸ Kế hoạch nhân sự; «Xem danh sách» liệt kê người đang làm của nhóm.
 */
export function HeadcountPlanReportPage() {
  return <ReportAnalyticsPage config={CONFIG} />
}
