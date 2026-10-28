import { appRoutes } from '@/shared/constants/app-routes'

import { ReportDepartmentFilter } from '../components/report-department-filter'
import type { ReportPageConfig } from '../types/report-analytics'
import { ReportAnalyticsPage } from './report-analytics-page'

const CONFIG: ReportPageConfig = {
  endpoint: '/api/profile-change-report/summary',
  exportEndpoint: '/api/profile-change-report/summary/export',
  drilldownEndpoint: '/api/profile-change-report/summary/rows',
  entity: 'employee',
  title: 'Yêu cầu sửa hồ sơ',
  description:
    'Đề nghị sửa hồ sơ nhân viên tự gửi trong kỳ (theo ngày gửi): đang chờ, chờ quá 2 ngày, đã duyệt, bị từ chối và thời gian xử lý bình quân. «Xem theo Trường bị xin sửa» đếm mỗi trường một lần nên tổng có thể lớn hơn số yêu cầu. Danh sách không hiện giá trị cũ / mới của trường.',
  slug: 'profile-changes',
  sourcePath: appRoutes.hr.profileChangeRequests,
  kpis: ['requests', 'pending', 'pending_over_2d', 'turnaround_hours'],
  tableMetrics: ['approved', 'rejected', 'reject_rate'],
  chartMetric: 'requests',
  defaultGroupBy: 'department',
  extraFilters: ReportDepartmentFilter,
}

/**
 * Yêu cầu sửa hồ sơ (E2, duoc-CR-689, khóa 27). Backend gác `employee.read` + khóa báo cáo 27 +
 * phạm vi hồ sơ; danh sách bấm số không trả giá trị cũ / mới (có thể là CCCD, tài khoản ngân hàng).
 */
export function ProfileChangesReportPage() {
  return <ReportAnalyticsPage config={CONFIG} />
}
