import { appRoutes } from '@/shared/constants/app-routes'

import type { ReportPageConfig } from '../types/report-analytics'
import { ReportAnalyticsPage } from './report-analytics-page'

const CONFIG: ReportPageConfig = {
  endpoint: '/api/purchase-progress/summary',
  exportEndpoint: '/api/purchase-progress/summary/export',
  entity: 'purchase_request',
  title: 'Tiến độ mua hàng',
  description: 'Giao hàng đúng hẹn, dòng chưa nhận đủ, NCC trễ — so với kỳ trước.',
  slug: 'purchase-progress',
  sourcePath: appRoutes.procurement.purchaseProgress,
  kpis: ['lines', 'deliveries', 'on_time_rate', 'unreceived_items', 'late_deliveries'],
  chartMetric: 'deliveries',
  defaultGroupBy: 'progress_status',
  breakdowns: [
    { key: 'supplier', title: 'Top nhà cung cấp' },
    { key: 'department', title: 'Top bộ phận' },
  ],
}

/**
 * Tiến độ mua hàng — bản BIỂU ĐỒ (P03). Trả lời: giao đúng hẹn tới đâu, dòng
 * nào chưa nhận đủ, NCC nào đứng đầu, bộ phận nào còn nhiều việc mở. Bảng theo
 * từng lần giao vẫn ở Thu mua (`sourcePath`).
 *
 * Chỉ số giao (lần giao/trễ/đúng hạn) tính theo lần giao của các ĐMH ĐẶT trong
 * kỳ (gộp theo ngày đặt), không lọc riêng theo ngày nhận — xem `notes` backend
 * trả về.
 */
export function PurchaseProgressChartPage() {
  return <ReportAnalyticsPage config={CONFIG} />
}
