import { appRoutes } from '@/shared/constants/app-routes'

import type { ReportPageConfig } from '../types/report-analytics'
import { ReportAnalyticsPage } from './report-analytics-page'

const CONFIG: ReportPageConfig = {
  endpoint: '/api/survey-progress/summary',
  exportEndpoint: '/api/survey-progress/summary/export',
  entity: 'survey_request',
  title: 'Tiến độ báo giá',
  description: 'Dòng yêu cầu báo giá đang mở, trễ hạn, NSTM đang xử lý — so với kỳ trước.',
  slug: 'survey-progress',
  sourcePath: appRoutes.procurement.surveyProgress,
  kpis: ['lines', 'open_lines', 'late', 'avg_handling_days'],
  chartMetric: 'lines',
  defaultGroupBy: 'progress',
  //  `handling_days_sum`/`handling_days_count` (mẫu số của `avg_handling_days`)
  //  nay backend tự đánh dấu `helper: true` trong `meta.metrics` — không cấu
  //  hình ẩn tay ở đây nữa (`hiddenMetrics` đã bỏ).
  breakdowns: [
    { key: 'assignee', title: 'Top NSTM' },
    { key: 'item_group', title: 'Top nhóm hàng' },
  ],
}

/**
 * Tiến độ báo giá — bản BIỂU ĐỒ (P03). Trả lời: còn bao nhiêu dòng yêu cầu báo
 * giá đang mở, trễ hạn ở đâu, NSTM nào đang ôm nhiều. Bảng từng dòng vẫn ở Thu
 * mua (`sourcePath`).
 */
export function SurveyProgressChartPage() {
  return <ReportAnalyticsPage config={CONFIG} />
}
