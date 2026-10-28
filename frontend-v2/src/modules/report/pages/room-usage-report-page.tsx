import { appRoutes } from '@/shared/constants/app-routes'

import { ReportDepartmentFilter } from '../components/report-department-filter'
import type { ReportPageConfig } from '../types/report-analytics'
import { ReportAnalyticsPage } from './report-analytics-page'

const CONFIG: ReportPageConfig = {
  endpoint: '/api/room-usage/summary',
  exportEndpoint: '/api/room-usage/summary/export',
  drilldownEndpoint: '/api/room-usage/summary/rows',
  entity: 'room_booking',
  title: 'Sử dụng phòng họp',
  description:
    'Lượt đặt và giờ đã đặt (chỉ lịch đã duyệt) so với giờ làm việc của phòng: tỷ lệ lấp đầy, tỷ lệ đặt rồi hủy / bị từ chối, số người dự bình quân so với sức chứa. Ô Phòng ban lọc theo phòng ban của người đặt.',
  slug: 'room-usage',
  sourcePath: appRoutes.hr.roomBookings,
  kpis: ['bookings', 'booked_hours', 'occupancy', 'cancel_rate'],
  tableMetrics: ['cancelled', 'attendees_avg', 'capacity_use'],
  chartMetric: 'booked_hours',
  defaultGroupBy: 'room',
  defaultPreset: 'this_month',
  extraFilters: ReportDepartmentFilter,
}

/**
 * Sử dụng phòng họp (F1, duoc-CR-689, khóa 28). «Xem theo Khung giờ» / «Thứ trong tuần» cho
 * thấy giờ cao điểm — chỗ để quyết có cần thêm phòng hay không.
 */
export function RoomUsageReportPage() {
  return <ReportAnalyticsPage config={CONFIG} />
}
