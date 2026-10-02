import { appRoutes } from '@/shared/constants/app-routes'

import type { ReportPageConfig } from '../types/report-analytics'
import { ReportAnalyticsPage } from './report-analytics-page'

const CONFIG: ReportPageConfig = {
  endpoint: '/api/survey-report/summary',
  exportEndpoint: '/api/survey-report/summary/export',
  entity: 'survey',
  title: 'Báo cáo khảo sát',
  description: 'Khảo sát NCC và sản phẩm, kết quả duyệt — so với kỳ trước.',
  slug: 'survey-report',
  sourcePath: appRoutes.procurement.surveyReport,
  kpis: ['lines', 'lines_supplier', 'lines_product', 'approved_rate'],
  chartMetric: 'lines',
  defaultGroupBy: 'line_approve',
  //  Nguồn này KHÔNG lọc theo công ty ở backend — ẩn ô Công ty kẻo trông như lọc được.
  hideCompany: true,
  breakdowns: [
    { key: 'nspt', title: 'Top NSPT' },
    { key: 'item_group', title: 'Top nhóm hàng' },
  ],
}

/**
 * Báo cáo khảo sát — bản BIỂU ĐỒ (P03). Trả lời: khảo sát được bao nhiêu NCC /
 * sản phẩm, duyệt được bao nhiêu, NSPT nào làm nhiều. Bảng từng dòng vẫn ở Thu
 * mua (`sourcePath`).
 */
export function SurveyReportChartPage() {
  return <ReportAnalyticsPage config={CONFIG} />
}
