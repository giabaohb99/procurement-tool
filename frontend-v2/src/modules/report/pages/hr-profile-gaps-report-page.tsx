import { appRoutes } from '@/shared/constants/app-routes'

import { ReportDepartmentFilter } from '../components/report-department-filter'
import type { ReportPageConfig } from '../types/report-analytics'
import { ReportAnalyticsPage } from './report-analytics-page'

const CONFIG: ReportPageConfig = {
  endpoint: '/api/employees/profile-gaps/summary',
  exportEndpoint: '/api/employees/profile-gaps/summary/export',
  drilldownEndpoint: '/api/employees/profile-gaps/summary/rows',
  entity: 'employee',
  title: 'Hồ sơ & tài khoản còn thiếu',
  description:
    'Nhân sự đang làm còn thiếu ngày vào làm, chức vụ, quản lý, giấy tờ; tài khoản chưa mở hoặc còn mở sau khi nghỉ.',
  slug: 'hr-profile-gaps',
  sourcePath: appRoutes.hr.employees,
  //  `resigned_active_account` chỉ có khi người xem có `user.read` — thiếu quyền thì backend
  //  gỡ khỏi `meta`, hàng thẻ tự co lại (`ReportKpiRow` bỏ khóa vắng mặt).
  kpis: ['active_total', 'complete_rate', 'missing_hire_date', 'resigned_active_account'],
  chartMetric: 'active_total',
  defaultGroupBy: 'department',
  breakdowns: [{ key: 'gap_kind', title: 'Theo loại còn thiếu' }],
  extraFilters: ReportDepartmentFilter,
  hideTrend: true,
  //  Tình trạng HIỆN TẠI — backend bỏ qua kỳ; ẩn nút Kỳ để khỏi tưởng đổi kỳ là đổi số.
  hidePeriod: true,
}

/**
 * Báo cáo Hồ sơ & tài khoản còn thiếu (duoc-CR-686, khóa 18). Nhóm thiếu giấy tờ nhạy cảm
 * chỉ hiện khi có `employee_sensitive.read`, nhóm tài khoản khi có `user.read` — backend
 * gỡ chỉ số khỏi `meta` và ghi một dòng `notes`, giao diện không tự gác thêm.
 */
export function HrProfileGapsReportPage() {
  return <ReportAnalyticsPage config={CONFIG} />
}
