import { appRoutes } from '@/shared/constants/app-routes'

import type { ReportPageConfig } from '../types/report-analytics'
import { ReportAnalyticsPage } from './report-analytics-page'

const CONFIG: ReportPageConfig = {
  endpoint: '/api/reports/procurement/summary',
  exportEndpoint: '/api/reports/procurement/summary/export',
  entity: 'report',
  title: 'Báo cáo mua hàng',
  description: 'Chi phí, giá trị đặt hàng, giao đúng hạn và công nợ mua hàng — so với kỳ trước.',
  slug: 'purchase-report',
  sourcePath: appRoutes.procurement.purchaseReport,
  kpis: ['spend', 'order_value', 'po_count', 'on_time_rate', 'debt_overdue'],
  chartMetric: 'spend',
  defaultGroupBy: 'department',
  //  `deliveries_done` (mẫu số của `on_time_rate`) và các chỉ số công nợ theo
  //  kỳ so sánh trước đây được ẩn tay qua `hiddenMetrics` — nay backend tự
  //  đánh dấu bằng `meta.metrics[].helper`/`snapshot`, không cấu hình ở đây nữa.
  breakdowns: [
    { key: 'supplier', title: 'Top nhà cung cấp' },
    { key: 'nspt', title: 'Top NSPT' },
    { key: 'department', title: 'Top bộ phận' },
    { key: 'item_group', title: 'Top nhóm hàng' },
  ],
}

/**
 * Báo cáo mua hàng — cấu hình mỏng dùng khung chung `ReportAnalyticsPage` (P03).
 * Bảng ma trận 10 tab (vận chuyển, tồn kho, giá vốn nhập khẩu…) vẫn ở Thu mua
 * (`sourcePath`) — trang này chỉ là lát biểu đồ kiểu Haravan cho phần
 * chi phí · đặt hàng · giao hàng · công nợ.
 *
 * `spend`/`order_value` đến từ HAI nguồn khác cột ngày (công nợ theo
 * `incur_date`, ĐMH theo `order_date` — xem `notes` backend trả về, trang tự
 * hiện nguyên văn dưới thanh lọc) nên khi "Xem theo" bộ phận/nhóm hàng/NSPT,
 * phần chi phí mua gộp vào "(Chưa gắn)" — KHÔNG phải lỗi hiển thị.
 */
export function PurchaseReportChartPage() {
  return <ReportAnalyticsPage config={CONFIG} />
}
