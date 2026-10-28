import { appRoutes } from '@/shared/constants/app-routes'

import { ReportDepartmentFilter } from '../components/report-department-filter'
import type { ReportPageConfig } from '../types/report-analytics'
import { ReportAnalyticsPage } from './report-analytics-page'

const CONFIG: ReportPageConfig = {
  endpoint: '/api/payroll-fund/summary',
  exportEndpoint: '/api/payroll-fund/summary/export',
  drilldownEndpoint: '/api/payroll-fund/summary/rows',
  entity: 'labor_contract',
  title: 'Quỹ lương theo pháp nhân',
  description:
    'Lương cơ bản, phụ cấp và lương đóng BHXH của hợp đồng đang hiệu lực tại cuối kỳ. Đây là lương thỏa thuận trên hợp đồng, không phải lương thực trả; nhóm dưới 3 người bị che để không lộ lương từng người.',
  slug: 'payroll-fund',
  //  HĐLĐ không có màn danh sách riêng — nguồn là danh sách nhân sự, như báo cáo Hợp đồng
  //  lao động (khóa 17; ngoại lệ khóa gác có ghi ở `report-catalog.test.ts`).
  sourcePath: appRoutes.hr.employees,
  //  Hai thẻ cuối là phần KẾ HOẠCH (duoc-CR-689, nguồn: Nhân sự ▸ Kế hoạch nhân sự) — máy chủ
  //  chưa trả thì thẻ tự bỏ (khóa vắng khỏi `meta`), hàng thẻ về lại 4.
  kpis: ['payroll_total', 'people_paid', 'avg_payroll', 'insurance_total', 'planned_payroll', 'payroll_use_rate'],
  //  Hai thành phần của quỹ lương + phần còn dư so với kế hoạch hiện sẵn trên bảng; thấp nhất /
  //  cao nhất bật ở menu «Cột».
  tableMetrics: ['base_total', 'allowance_total', 'payroll_remaining'],
  chartMetric: 'payroll_total',
  //  Mỗi pháp nhân trả lương phần mình — mặc định xem theo công ty.
  defaultGroupBy: 'company',
  defaultPreset: 'this_month',
  extraFilters: ReportDepartmentFilter,
}

/**
 * Quỹ lương theo pháp nhân (A5, duoc-CR-688, khóa 21). Số tại mốc `min(cuối kỳ, hôm nay)`;
 * xu hướng = quỹ lương + số người tại cuối mỗi tháng trong kỳ. Nhóm dưới 3 người backend
 * trả `null` → ô hiện «—»; danh sách từng người của nhóm bị che trả 403 (thẻ lỗi của ngăn).
 */
export function PayrollFundReportPage() {
  return <ReportAnalyticsPage config={CONFIG} />
}
