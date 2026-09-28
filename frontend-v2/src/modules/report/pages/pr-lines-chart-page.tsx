import { appRoutes } from '@/shared/constants/app-routes'

import type { ReportPageConfig } from '../types/report-analytics'
import { ReportAnalyticsPage } from './report-analytics-page'

const CONFIG: ReportPageConfig = {
  endpoint: '/api/reports/pr-lines/summary',
  exportEndpoint: '/api/reports/pr-lines/summary/export',
  entity: 'report',
  title: 'Chi tiết YC mua hàng',
  description: 'Dòng hàng của yêu cầu mua hàng — soi phần chưa được đặt để không đặt sót đơn.',
  slug: 'pr-lines',
  sourcePath: appRoutes.procurement.prLinesReport,
  kpis: ['lines', 'amount', 'idle_lines', 'ordered_rate'],
  chartMetric: 'lines',
  defaultGroupBy: 'line_status',
  breakdowns: [
    { key: 'assignee', title: 'Top NSTM' },
    { key: 'department', title: 'Top bộ phận' },
    { key: 'item_group', title: 'Top nhóm hàng' },
  ],
}

/**
 * Chi tiết YC mua hàng — bản BIỂU ĐỒ của phân hệ Báo cáo (P03).
 *
 * Bảng theo từng dòng vẫn ở Thu mua (`sourcePath`): người mua hàng dùng nó để
 * soi TỪNG mã chưa đặt, việc đó biểu đồ không thay được. Trang này trả lời câu
 * hỏi của người quản lý: còn bao nhiêu dòng chưa đặt, dồn ở đâu, ai đang ôm.
 *
 * Số liệu BỎ dòng đã hủy (trừ "Tiến độ dòng" — vẫn đếm đủ để thấy tỷ lệ hủy,
 * xem `notes` backend trả về).
 */
export function PrLinesChartPage() {
  return <ReportAnalyticsPage config={CONFIG} />
}
