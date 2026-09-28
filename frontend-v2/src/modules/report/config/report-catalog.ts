import type { LucideIcon } from 'lucide-react'
import { BarChart3, ChartColumnBig, TextSearch, Truck } from 'lucide-react'
import type { ComponentType } from 'react'

import type { PermissionEntity } from '@/core/authorization/permission-types'
import { appRoutes } from '@/shared/constants/app-routes'

/** Một trang báo cáo gom về phân hệ Báo cáo. */
export interface ReportCatalogEntry {
  label: string
  /** Câu giới thiệu hiện trên thẻ ở trang Tổng quan báo cáo. */
  description: string
  /** Đường dẫn TRONG phân hệ Báo cáo (`/report/...`). */
  path: string
  /** Trang BẢNG gốc ở phân hệ chủ — khóa quyền phải khớp mục menu của nó (có test canh). */
  sourcePath: string
  icon: LucideIcon
  /** Khóa quyền — GIỐNG HỆT khóa của mục menu ở phân hệ gốc, lệch là lủng. */
  entity: PermissionEntity
  /** Tên phân hệ gốc — thành tiêu đề nhóm trên menu trái. */
  group: string
  /** Nạp trang biểu đồ — `import()` động để mỗi trang một chunk riêng. */
  load: () => Promise<ComponentType>
}

/**
 * DANH MỤC BÁO CÁO — nguồn DUY NHẤT dựng cả menu, route lẫn thẻ lối tắt của
 * phân hệ Báo cáo. Thêm một báo cáo mới = thêm một dòng ở đây (+ một đường ở
 * `appRoutes.report`).
 *
 * Mỗi báo cáo ở đây là bản BIỂU ĐỒ (trang riêng trong `report/pages/`), số liệu
 * từ một đường `/summary` dùng chung bộ lọc + phạm vi với bảng gốc. BẢNG từng
 * dòng vẫn ở phân hệ gốc (`sourcePath`) — người làm nghiệp vụ cần soi từng dòng,
 * việc đó biểu đồ không thay được — và mỗi trang biểu đồ có nút dẫn sang.
 */
export const REPORT_CATALOG: ReportCatalogEntry[] = [
  {
    label: 'Báo cáo mua hàng',
    description: 'Chi phí so năm trước, giao hàng, công nợ, Top NCC · bộ phận · nhóm hàng, vận chuyển.',
    path: appRoutes.report.purchaseReport,
    sourcePath: appRoutes.procurement.purchaseReport,
    icon: ChartColumnBig,
    entity: 'report',
    group: 'Thu mua',
    load: async () => (await import('../pages/purchase-report-chart-page')).PurchaseReportChartPage,
  },
  {
    label: 'Chi tiết YC mua hàng',
    description: 'Dòng chưa được đặt theo tháng, tiến độ, NSTM, bộ phận, nhóm hàng.',
    path: appRoutes.report.prLinesReport,
    sourcePath: appRoutes.procurement.prLinesReport,
    icon: TextSearch,
    entity: 'report',
    group: 'Thu mua',
    load: async () => (await import('../pages/pr-lines-chart-page')).PrLinesChartPage,
  },
  {
    label: 'Tiến độ báo giá',
    description: 'Dòng đang mở, trễ hạn, tiến độ xử lý, NSTM đang giữ việc.',
    path: appRoutes.report.surveyProgress,
    sourcePath: appRoutes.procurement.surveyProgress,
    icon: Truck,
    entity: 'survey_request',
    group: 'Thu mua',
    load: async () =>
      (await import('../pages/survey-progress-chart-page')).SurveyProgressChartPage,
  },
  {
    label: 'Tiến độ mua hàng',
    description: 'Giao đúng hạn, dòng chưa nhận đủ, NCC trễ, việc mở theo bộ phận.',
    path: appRoutes.report.purchaseProgress,
    sourcePath: appRoutes.procurement.purchaseProgress,
    icon: Truck,
    entity: 'purchase_request',
    group: 'Thu mua',
    load: async () =>
      (await import('../pages/purchase-progress-chart-page')).PurchaseProgressChartPage,
  },
  {
    label: 'Báo cáo khảo sát',
    description: 'Khảo sát NCC & sản phẩm theo tháng, kết quả duyệt, NSPT, nhóm hàng.',
    path: appRoutes.report.surveyReport,
    sourcePath: appRoutes.procurement.surveyReport,
    icon: BarChart3,
    entity: 'survey',
    group: 'Thu mua',
    load: async () => (await import('../pages/survey-report-chart-page')).SurveyReportChartPage,
  },
]
