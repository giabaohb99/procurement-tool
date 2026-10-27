import { appRoutes } from '@/shared/constants/app-routes'

import { ReportDepartmentFilter } from '../components/report-department-filter'
import type { ReportPageConfig } from '../types/report-analytics'
import { ReportAnalyticsPage } from './report-analytics-page'

const CONFIG: ReportPageConfig = {
  endpoint: '/api/labor-usage-report/summary',
  exportEndpoint: '/api/labor-usage-report/summary/export',
  exportLabel: 'Xuất mẫu 01/PLI',
  drilldownEndpoint: '/api/labor-usage-report/summary/rows',
  entity: 'employee',
  title: 'Báo cáo sử dụng lao động (01/PLI)',
  description:
    'Tình hình sử dụng lao động theo Mẫu số 01/PLI, mỗi pháp nhân một bản. Nộp Sở Nội vụ trước 05/6 và 05/12; cột chưa có dữ liệu để trống trong tệp — điền tay trước khi nộp.',
  slug: 'labor-usage-report',
  sourcePath: appRoutes.hr.employees,
  kpis: ['people', 'female', 'job_manager', 'job_high'],
  //  Cơ cấu vị trí việc làm + loại HĐ là phần chính của mẫu — hiện sẵn trên bảng, không lên thẻ.
  tableMetrics: ['job_mid', 'job_other', 'ct_indefinite', 'ct_fixed', 'ct_other'],
  //  Bắt buộc theo kiểu, nhưng không dùng: `hideTrend` (backend luôn trả `trend: []`).
  chartMetric: 'people',
  //  Mỗi pháp nhân tự nộp một mẫu riêng — mặc định xem theo công ty.
  defaultGroupBy: 'company',
  defaultPreset: 'this_year',
  extraFilters: ReportDepartmentFilter,
  hideTrend: true,
}

/**
 * Báo cáo tình hình sử dụng lao động, Mẫu số 01/PLI (duoc-CR-687, khóa 20). Cùng tập người
 * và cùng luật quyền với Sổ quản lý lao động (khóa 19); tệp xuất đúng khung 27 cột của mẫu,
 * cột hệ thống chưa có dữ liệu để trống và được liệt kê ở `notes`.
 */
export function LaborUsageReportPage() {
  return <ReportAnalyticsPage config={CONFIG} />
}
