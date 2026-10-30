import { appRoutes } from '@/shared/constants/app-routes'

import { PayrollFundMissingSalaryNotice } from '../components/payroll-fund-missing-salary-notice'
import { ReportDepartmentFilter } from '../components/report-department-filter'
import type { ReportPageConfig } from '../types/report-analytics'
import { ReportAnalyticsPage } from './report-analytics-page'

const CONFIG: ReportPageConfig = {
  endpoint: '/api/payroll-fund/summary',
  exportEndpoint: '/api/payroll-fund/summary/export',
  //  Danh sách người của một nhóm — KHÔNG có cột tiền (duoc-CR-693), chỉ để biết ai được tính.
  drilldownEndpoint: '/api/payroll-fund/summary/rows',
  //  duoc-CR-693: gác như backend — `employee.read` xem, `employee.export` xuất (+ khóa báo cáo 21).
  entity: 'employee',
  title: 'Quỹ lương theo pháp nhân',
  //  duoc-CR-693: nguồn đổi từ lương trên HĐLĐ sang ô lương nhập ở hồ sơ từng người.
  description:
    'Quỹ lương = lương + phụ cấp nhập ở hồ sơ từng người (số hiện tại). Chỉ hiện tổng theo pháp nhân, phòng ban, toàn công ty; nhóm dưới 3 người bị che. Không ai xem được lương từng người qua báo cáo.',
  slug: 'payroll-fund',
  //  Nguồn là ô lương trên hồ sơ — màn danh sách nhân sự.
  sourcePath: appRoutes.hr.employees,
  //  Khóa vắng khỏi `meta` thì thẻ tự bỏ (`ReportKpiRow`), lệch tên với backend không vỡ trang.
  kpis: ['payroll_total', 'base_total', 'allowance_total', 'people_paid', 'avg_payroll'],
  chartMetric: 'payroll_total',
  //  Mỗi pháp nhân trả lương phần mình — mặc định xem theo công ty.
  defaultGroupBy: 'company',
  extraFilters: ReportDepartmentFilter,
  //  Ảnh chụp HIỆN TẠI: không xu hướng, không so sánh kỳ — ẩn biểu đồ thời gian và nút Kỳ để
  //  khỏi tưởng đổi kỳ là đổi số (cùng khuôn Hồ sơ còn thiếu).
  hideTrend: true,
  hidePeriod: true,
  kpiNotice: PayrollFundMissingSalaryNotice,
}

/**
 * Quỹ lương theo pháp nhân (A5, khóa 21). Từ duoc-CR-693 số là lương + phụ cấp nhập ở hồ sơ, tại
 * thời điểm xem. Nhóm dưới 3 người backend trả `null` → ô hiện "—"; danh sách người không có tiền.
 */
export function PayrollFundReportPage() {
  return <ReportAnalyticsPage config={CONFIG} />
}
