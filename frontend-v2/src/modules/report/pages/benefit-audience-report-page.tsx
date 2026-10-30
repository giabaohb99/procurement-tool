import { appRoutes } from '@/shared/constants/app-routes'

import { BenefitAudienceFilters } from '../components/benefit-audience-filters'
import type { ReportPageConfig } from '../types/report-analytics'
import { BENEFIT_DEFAULT_PRESET, BENEFIT_PARAM } from '../utils/benefit-occasion-presets'
import { ReportAnalyticsPage } from './report-analytics-page'

const CONFIG: ReportPageConfig = {
  endpoint: '/api/benefit-audience/summary',
  exportEndpoint: '/api/benefit-audience/summary/export',
  exportLabel: 'Xuất danh sách ký nhận',
  drilldownEndpoint: '/api/benefit-audience/summary/rows',
  entity: 'employee',
  title: 'Phúc lợi & sự kiện',
  description:
    'Ai được nhận quà dịp này và tổng kinh phí — tính người đang làm vào ngày dịp. Chọn dịp có sẵn hoặc tự đặt điều kiện, nhập mức quà rồi xuất danh sách ký nhận, mỗi pháp nhân một sheet.',
  slug: 'benefit-audience',
  sourcePath: appRoutes.hr.employees,
  //  `children` chỉ có khi lọc theo con (`child_max_age`) — vắng khỏi `meta` thì thẻ tự co lại.
  kpis: ['people', 'budget', 'managers', 'children'],
  tableMetrics: ['staff'],
  //  Bắt buộc theo kiểu, nhưng không dùng: `hideTrend` (backend luôn trả `trend: []`).
  chartMetric: 'people',
  //  Mỗi pháp nhân hạch toán phần quà của mình.
  defaultGroupBy: 'company',
  defaultPreset: BENEFIT_DEFAULT_PRESET,
  extraFilters: BenefitAudienceFilters,
  //  Tắt "Tính người đang nghỉ" đòi `leave_request.read` — thiếu quyền thì bỏ tham số (link chia sẻ).
  paramsRequirePermission: { [BENEFIT_PARAM.includeOnLeave]: ['leave_request', 'read'] },
  hideTrend: true,
  //  Kỳ = MỘT ngày dịp, chọn ở ô "Ngày dịp" trong khung lọc — ẩn nút Kỳ báo cáo để không có
  //  hai chỗ cùng đặt một thứ.
  hidePeriod: true,
}

/**
 * Phúc lợi & sự kiện (H1, duoc-CR-688, khóa 22). Mức quà nhập tay trên màn, KHÔNG lưu đợt
 * phát. Lọc theo tuổi / tháng sinh / tuổi con đòi `employee_sensitive.read` — thiếu thì
 * backend trả 403 câu dễ hiểu, trang hiện ở thẻ lỗi; nút "Bỏ hết điều kiện" trong khung lọc
 * là lối thoát (thẻ lỗi chỉ đặt lại "Xem theo").
 */
export function BenefitAudienceReportPage() {
  return <ReportAnalyticsPage config={CONFIG} />
}
