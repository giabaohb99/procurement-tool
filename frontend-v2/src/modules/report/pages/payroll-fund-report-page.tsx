import { appRoutes } from '@/shared/constants/app-routes'

import { PayrollFundMissingContractNotice } from '../components/payroll-fund-missing-contract-notice'
import { ReportDepartmentFilter } from '../components/report-department-filter'
import type { ReportPageConfig } from '../types/report-analytics'
import { ReportAnalyticsPage } from './report-analytics-page'

const CONFIG: ReportPageConfig = {
  endpoint: '/api/payroll-fund/summary',
  exportEndpoint: '/api/payroll-fund/summary/export',
  drilldownEndpoint: '/api/payroll-fund/summary/rows',
  entity: 'labor_contract',
  title: 'Quỹ lương theo pháp nhân',
  //  duoc-CR-692: Kế hoạch nhân sự đã bỏ — quỹ lương CHỈ tính từ lương trên HĐLĐ của từng người.
  description:
    'Quỹ lương = lương cơ bản + phụ cấp trên hợp đồng lao động đang hiệu lực của từng người; xem theo phòng ban, pháp nhân; dòng Tổng là toàn công ty. Nhóm dưới 3 người bị che để không lộ lương từng người.',
  slug: 'payroll-fund',
  //  HĐLĐ không có màn danh sách riêng — nguồn là danh sách nhân sự, như báo cáo Hợp đồng
  //  lao động (khóa 17; ngoại lệ khóa gác có ghi ở `report-catalog.test.ts`).
  sourcePath: appRoutes.hr.employees,
  kpis: ['payroll_total', 'people_paid', 'avg_payroll', 'insurance_total'],
  //  Hai thành phần của quỹ lương hiện sẵn trên bảng; thấp nhất / cao nhất bật ở menu «Cột».
  tableMetrics: ['base_total', 'allowance_total'],
  chartMetric: 'payroll_total',
  //  Mỗi pháp nhân trả lương phần mình — mặc định xem theo công ty.
  defaultGroupBy: 'company',
  defaultPreset: 'this_month',
  extraFilters: ReportDepartmentFilter,
  kpiNotice: PayrollFundMissingContractNotice,
}

/**
 * Quỹ lương theo pháp nhân (A5, duoc-CR-688, khóa 21). Số tại mốc `min(cuối kỳ, hôm nay)`;
 * xu hướng = quỹ lương + số người tại cuối mỗi tháng trong kỳ. Nhóm dưới 3 người backend
 * trả `null` → ô hiện «—»; danh sách từng người của nhóm bị che trả 403 (thẻ lỗi của ngăn).
 */
export function PayrollFundReportPage() {
  return <ReportAnalyticsPage config={CONFIG} />
}
