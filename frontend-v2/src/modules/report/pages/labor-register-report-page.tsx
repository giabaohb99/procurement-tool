import { appRoutes } from '@/shared/constants/app-routes'

import { ReportDepartmentFilter } from '../components/report-department-filter'
import type { ReportPageConfig } from '../types/report-analytics'
import { ReportAnalyticsPage } from './report-analytics-page'

const CONFIG: ReportPageConfig = {
  endpoint: '/api/labor-register/summary',
  exportEndpoint: '/api/labor-register/summary/export',
  exportLabel: 'Xuất sổ (Excel)',
  drilldownEndpoint: '/api/labor-register/summary/rows',
  entity: 'employee',
  title: 'Sổ quản lý lao động',
  description:
    'Người làm việc trong kỳ, đang làm cuối kỳ, nghỉ việc trong kỳ, hồ sơ còn thiếu thông tin bắt buộc của sổ — xuất sổ mỗi pháp nhân một sheet.',
  slug: 'labor-register',
  sourcePath: appRoutes.hr.employees,
  kpis: ['people', 'working', 'left_in_period', 'missing_required'],
  //  Bắt buộc theo kiểu, nhưng không dùng: `hideTrend` (backend luôn trả `trend: []`).
  chartMetric: 'people',
  defaultGroupBy: 'department',
  defaultPreset: 'this_year',
  extraFilters: ReportDepartmentFilter,
  hideTrend: true,
}

/**
 * Sổ quản lý lao động (duoc-CR-687, khóa 19). Tập người = ai làm việc ở BẤT KỲ lúc nào
 * trong kỳ. Tệp xuất chứa CCCD, BHXH, ngày sinh, lương — backend đòi thêm
 * `employee_sensitive.read` + `labor_contract.read` (thiếu thì 403 nói rõ thiếu gì, trang
 * hiện câu đó kèm nút đặt lại); giao diện không tự gác thêm.
 */
export function LaborRegisterReportPage() {
  return <ReportAnalyticsPage config={CONFIG} />
}
