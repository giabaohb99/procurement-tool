import { appRoutes } from '@/shared/constants/app-routes'

import type { ReportPageConfig } from '../types/report-analytics'
import { ReportAnalyticsPage } from './report-analytics-page'

const CONFIG: ReportPageConfig = {
  endpoint: '/api/vehicle-bookings/summary',
  exportEndpoint: '/api/vehicle-bookings/summary/export',
  entity: 'vehicle_booking',
  title: 'Báo cáo đặt xe',
  description: 'Chuyến hoàn thành, tỷ lệ từ chối/hủy, chi phí, thời gian duyệt — theo xe, tài xế, bộ phận.',
  slug: 'dat-xe',
  sourcePath: appRoutes.vehicleBooking.requests,
  kpis: ['requests', 'completed', 'reject_cancel_rate', 'avg_approval_hours'],
  chartMetric: 'requests',
  defaultGroupBy: 'status',
  breakdowns: [
    { key: 'status', title: 'Theo trạng thái' },
    { key: 'request_type', title: 'Theo loại yêu cầu' },
  ],
}

/**
 * Báo cáo Đặt xe (phase 05, 5.1) — bản BIỂU ĐỒ kiểu Haravan của phân hệ Đặt xe.
 *
 * Kỳ tính theo NGÀY ĐI (`start_time`, Q5.1), không phải ngày tạo phiếu. Khác
 * `/vehicle-bookings/overview` (bảng điều khiển THEO VAI — Chuyến của tôi / Việc
 * điều phối…): trang này lọc theo kỳ + so sánh, dùng CHUNG `require`/`apply_scope`
 * với danh sách Yêu cầu đặt xe (`sourcePath`).
 */
export function VehicleBookingReportPage() {
  return <ReportAnalyticsPage config={CONFIG} />
}
