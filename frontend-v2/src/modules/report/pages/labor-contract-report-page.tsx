import { appRoutes } from '@/shared/constants/app-routes'

import { ReportDepartmentFilter } from '../components/report-department-filter'
import type { ReportPageConfig } from '../types/report-analytics'
import { ReportAnalyticsPage } from './report-analytics-page'

const CONFIG: ReportPageConfig = {
  endpoint: '/api/labor-contracts/summary',
  exportEndpoint: '/api/labor-contracts/summary/export',
  drilldownEndpoint: '/api/labor-contracts/summary/rows',
  entity: 'labor_contract',
  title: 'Hợp đồng lao động',
  description:
    'HĐ đang hiệu lực, sắp hết hạn, đã quá hạn mà người vẫn đi làm, nhân sự chưa có HĐ — xem theo công ty, phòng ban, loại hợp đồng.',
  slug: 'labor-contract',
  //  HĐLĐ không có màn danh sách riêng — nằm ở tab «Hợp đồng» của hồ sơ nhân sự.
  sourcePath: appRoutes.hr.employees,
  kpis: ['active', 'expiring_30', 'overdue', 'no_contract'],
  //  Bắt buộc theo kiểu, nhưng không dùng: `hideTrend` (backend luôn trả `trend: []`).
  chartMetric: 'active',
  defaultGroupBy: 'department',
  breakdowns: [{ key: 'contract_type', title: 'Theo loại hợp đồng' }],
  extraFilters: ReportDepartmentFilter,
  hideTrend: true,
}

/**
 * Báo cáo Hợp đồng lao động (duoc-CR-686, khóa 17). Trạng thái từng HĐ tính tại
 * `min(cuối kỳ, hôm nay)` — chọn kỳ đã qua là xem lại tình hình tại cuối kỳ đó. Danh
 * sách có LƯƠNG (cơ bản · đóng BHXH · phụ cấp): ai có `labor_contract.read` thì thấy,
 * cùng luật với tab HĐ của hồ sơ nhân sự.
 */
export function LaborContractReportPage() {
  return <ReportAnalyticsPage config={CONFIG} />
}
