import { appRoutes } from '@/shared/constants/app-routes'

import type { ReportPageConfig } from '../types/report-analytics'
import { ReportAnalyticsPage } from './report-analytics-page'

const CONFIG: ReportPageConfig = {
  endpoint: '/api/leave-requests/summary',
  exportEndpoint: '/api/leave-requests/summary/export',
  entity: 'leave_request',
  title: 'Tình hình nghỉ phép',
  description:
    'Số đơn, ngày nghỉ đã duyệt/đang chờ, số người nghỉ, tỷ lệ từ chối-trả về, thời gian duyệt trung bình.',
  slug: 'leave-usage',
  sourcePath: appRoutes.hr.leaveRequests,
  kpis: ['requests', 'days_approved', 'people_on_leave', 'reject_return_rate', 'avg_turnaround_hours'],
  chartMetric: 'days_approved',
  defaultGroupBy: 'leave_type',
  breakdowns: [
    //  Backend xếp loại nghỉ theo NGÀY đã duyệt (loại chỉ nằm ở dòng phụ không bị rớt), không theo số đơn.
    { key: 'leave_type', title: 'Top loại nghỉ', rankMetric: 'days_approved' },
    { key: 'status', title: 'Theo trạng thái' },
  ],
}

/**
 * Báo cáo Nghỉ phép — tình hình nghỉ (phase 04). Đơn khai NHIỀU loại nghỉ góp
 * mặt ở mọi nhóm loại nghỉ có dòng tương ứng ("Xem theo" Loại nghỉ), nhưng
 * Tổng/"Số đơn"/"Số người nghỉ" chỉ đếm 1 đơn — xem `notes` backend trả về.
 */
export function LeaveUsageReportPage() {
  return <ReportAnalyticsPage config={CONFIG} />
}
