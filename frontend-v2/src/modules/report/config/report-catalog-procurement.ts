import { BarChart3, ChartColumnBig, TextSearch, Truck } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'

import type { ReportCatalogEntry } from './report-catalog'

/**
 * Nhóm THU MUA của danh mục báo cáo (P03) — 5 báo cáo dời từ 5 trang biểu đồ
 * viết tay cũ sang khung `ReportAnalyticsPage`; mỗi báo cáo giờ chỉ còn một
 * `ReportPageConfig` (`pages/*-chart-page.tsx`, xem tệp đó để biết KPI/chỉ số
 * xu hướng/breakdown/nhóm mặc định). BẢNG từng dòng vẫn ở phân hệ gốc
 * (`sourcePath`) — người làm nghiệp vụ cần soi từng dòng, biểu đồ không thay
 * được việc đó.
 */
export const PROCUREMENT_REPORT_CATALOG: ReportCatalogEntry[] = [
  {
    label: 'Báo cáo mua hàng',
    description:
      'Chi phí, giá trị đặt hàng, giao đúng hạn, công nợ — Top NCC · NSPT · bộ phận · nhóm hàng.',
    path: appRoutes.report.purchaseReport,
    sourcePath: appRoutes.procurement.purchaseReport,
    icon: ChartColumnBig,
    //  ReportKey.PURCHASE_REPORT (backend) = 1.
    key: 1,
    entity: 'report',
    group: 'Thu mua',
    endpoint: '/api/reports/procurement/summary',
    overviewKpis: ['spend', 'on_time_rate'],
    load: async () => (await import('../pages/purchase-report-chart-page')).PurchaseReportChartPage,
  },
  {
    label: 'Chi tiết YC mua hàng',
    description: 'Dòng chưa được đặt theo tiến độ, bộ phận, nhóm hàng, NSTM đang giữ.',
    path: appRoutes.report.prLinesReport,
    sourcePath: appRoutes.procurement.prLinesReport,
    icon: TextSearch,
    //  ReportKey.PR_LINES (backend) = 2.
    key: 2,
    entity: 'report',
    group: 'Thu mua',
    endpoint: '/api/reports/pr-lines/summary',
    overviewKpis: ['idle_lines'],
    load: async () => (await import('../pages/pr-lines-chart-page')).PrLinesChartPage,
  },
  {
    label: 'Tiến độ báo giá',
    description: 'Dòng đang mở, trễ hạn, ngày xử lý trung bình, NSTM đang giữ việc.',
    path: appRoutes.report.surveyProgress,
    sourcePath: appRoutes.procurement.surveyProgress,
    icon: Truck,
    //  ReportKey.SURVEY_PROGRESS (backend) = 3.
    key: 3,
    entity: 'survey_request',
    group: 'Thu mua',
    endpoint: '/api/survey-progress/summary',
    overviewKpis: ['late'],
    load: async () => (await import('../pages/survey-progress-chart-page')).SurveyProgressChartPage,
  },
  {
    label: 'Tiến độ mua hàng',
    description: 'Giao đúng hạn, dòng chưa nhận đủ, NCC trễ, việc mở theo bộ phận.',
    path: appRoutes.report.purchaseProgress,
    sourcePath: appRoutes.procurement.purchaseProgress,
    icon: Truck,
    //  ReportKey.PURCHASE_PROGRESS (backend) = 4.
    key: 4,
    entity: 'purchase_request',
    group: 'Thu mua',
    endpoint: '/api/purchase-progress/summary',
    //  KHÔNG lấy `on_time_rate` — Báo cáo mua hàng đã có thẻ «Giao đúng hạn» cùng tên trên Tổng quan.
    overviewKpis: ['late_deliveries'],
    load: async () =>
      (await import('../pages/purchase-progress-chart-page')).PurchaseProgressChartPage,
  },
  {
    label: 'Báo cáo khảo sát',
    description: 'Khảo sát NCC & sản phẩm, kết quả duyệt, theo NSPT và nhóm hàng.',
    path: appRoutes.report.surveyReport,
    sourcePath: appRoutes.procurement.surveyReport,
    icon: BarChart3,
    //  ReportKey.SURVEY_REPORT (backend) = 5.
    key: 5,
    entity: 'survey',
    group: 'Thu mua',
    endpoint: '/api/survey-report/summary',
    //  Khớp `hideCompany: true` của `survey-report-chart-page.tsx` — nguồn này
    //  không lọc theo công ty ở backend.
    hideCompany: true,
    overviewKpis: ['approved_rate'],
    load: async () => (await import('../pages/survey-report-chart-page')).SurveyReportChartPage,
  },
]
