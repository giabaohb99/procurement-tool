import { appRoutes } from '@/shared/constants/app-routes'

import { ReportDepartmentFilter } from '../components/report-department-filter'
import type { ReportPageConfig } from '../types/report-analytics'
import { ReportAnalyticsPage } from './report-analytics-page'

const CONFIG: ReportPageConfig = {
  endpoint: '/api/legal-watch/summary',
  exportEndpoint: '/api/legal-watch/summary/export',
  drilldownEndpoint: '/api/legal-watch/summary/rows',
  entity: 'employee',
  title: 'Đối tượng cần chú ý theo luật',
  description:
    'Tại mốc cuối kỳ (hoặc hôm nay nếu cuối kỳ ở tương lai): người đến tuổi nghỉ hưu trong 12 tháng tới theo lộ trình Nghị định 135/2020 (mốc = hết tháng đủ tuổi), người đã quá tuổi nghỉ hưu vẫn đang làm, người đang nghỉ thai sản, lao động nữ nuôi con dưới 12 tháng. Cần thêm quyền xem thông tin nhạy cảm của hồ sơ; danh sách chỉ hiện ngày mốc, không hiện ngày sinh.',
  slug: 'legal-watch',
  sourcePath: appRoutes.hr.employees,
  kpis: ['retire_12m', 'past_retirement', 'maternity_now', 'child_under_12m'],
  //  Bắt buộc theo kiểu, nhưng không dùng cho xu hướng: `hideTrend` (tình trạng tại một mốc).
  chartMetric: 'retire_12m',
  defaultGroupBy: 'department',
  extraFilters: ReportDepartmentFilter,
  hideTrend: true,
}

/**
 * Đối tượng cần chú ý theo luật (B4, duoc-CR-689, khóa 29). Backend đòi thêm
 * `employee_sensitive.read` (ngày sinh, con nhỏ) → thiếu thì 403 kèm câu dễ hiểu, trang hiện thẻ lỗi.
 */
export function LegalWatchReportPage() {
  return <ReportAnalyticsPage config={CONFIG} />
}
