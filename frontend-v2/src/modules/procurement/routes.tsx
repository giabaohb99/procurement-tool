import {
  BarChart3,
  ChartColumnBig,
  ClipboardCheck,
  ClipboardList,
  FileText,
  LayoutDashboard,
  ShoppingCart,
  Truck,
  UserCheck,
} from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Phân hệ THU MUA — luồng chứng từ: yêu cầu báo giá → khảo sát → yêu cầu mua
 * hàng → đơn mua hàng → tiến độ nhận hàng.
 *
 * Danh mục NHÀ CUNG CẤP không nằm ở đây mà thuộc phân hệ Sản xuất; bên này chỉ
 * đọc lại dữ liệu NCC trên chứng từ.
 *
 * Trang nạp bằng `lazy` để mỗi phân hệ thành một chunk riêng: người dùng chỉ tải
 * phần mình mở, gói khởi động không phình theo số module.
 */
export const procurementModule: ErpModule = {
  id: 'procurement',
  title: 'Thu mua',
  description: 'Yêu cầu báo giá, khảo sát, yêu cầu và đơn mua hàng.',
  icon: ShoppingCart,
  path: appRoutes.procurement.root,
  accent: 'bg-sky-500/10 text-sky-600 dark:text-sky-400',
  enabled: true,
  entity: 'purchase_request',

  nav: [
    {
      label: 'Tổng quan',
      path: appRoutes.procurement.root,
      icon: LayoutDashboard,
      end: true,
    },
    {
      label: 'Yêu cầu báo giá',
      path: appRoutes.procurement.surveyRequests,
      icon: ClipboardList,
      entity: 'survey_request',
      group: 'Mua hàng',
    },
    {
      label: 'Yêu cầu mua hàng',
      path: appRoutes.procurement.purchaseRequests,
      icon: FileText,
      entity: 'purchase_request',
      group: 'Mua hàng',
    },
    {
      label: 'Đơn mua hàng',
      path: appRoutes.procurement.purchaseOrders,
      icon: ShoppingCart,
      entity: 'purchase_order',
      group: 'Mua hàng',
    },
    {
      label: 'Tiến độ mua hàng',
      path: appRoutes.procurement.purchaseProgress,
      icon: Truck,
      entity: 'purchase_request',
      group: 'Mua hàng',
    },
    {
      label: 'Báo cáo mua hàng',
      path: appRoutes.procurement.purchaseReport,
      icon: ChartColumnBig,
      entity: 'report',
      group: 'Mua hàng',
    },
    {
      label: 'Phiếu khảo sát',
      path: appRoutes.procurement.surveys,
      icon: ClipboardCheck,
      entity: 'survey',
      group: 'Khảo sát',
    },
    {
      label: 'Báo cáo khảo sát',
      path: appRoutes.procurement.surveyReport,
      icon: BarChart3,
      entity: 'survey',
      group: 'Khảo sát',
    },
    {
      label: 'Phân công phụ trách',
      path: appRoutes.procurement.categoryAssignees,
      icon: UserCheck,
      entity: 'category_assignee',
      manage: true,
      group: 'Cấu hình',
    },
  ],

  routes: [
    {
      path: appRoutes.procurement.root,
      lazy: async () => ({
        Component: (await import('./pages/procurement-dashboard-page'))
          .ProcurementDashboardPage,
      }),
    },
    {
      path: appRoutes.procurement.surveyRequests,
      lazy: async () => ({
        Component: (await import('./pages/survey-request-list-page')).SurveyRequestListPage,
      }),
    },
    {
      path: appRoutes.procurement.surveyRequestNew,
      lazy: async () => ({
        Component: (await import('./pages/survey-request-detail-page')).SurveyRequestDetailPage,
      }),
    },
    {
      path: appRoutes.procurement.surveyRequestDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/survey-request-detail-page')).SurveyRequestDetailPage,
      }),
    },
    {
      path: appRoutes.procurement.purchaseRequests,
      lazy: async () => ({
        Component: (await import('./pages/purchase-request-list-page'))
          .PurchaseRequestListPage,
      }),
    },
    {
      path: appRoutes.procurement.purchaseRequestNew,
      lazy: async () => ({
        Component: (await import('./pages/purchase-request-detail-page'))
          .PurchaseRequestDetailPage,
      }),
    },
    {
      path: appRoutes.procurement.purchaseRequestDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/purchase-request-detail-page'))
          .PurchaseRequestDetailPage,
      }),
    },
    {
      path: appRoutes.procurement.purchaseOrders,
      lazy: async () => ({
        Component: (await import('./pages/purchase-order-list-page')).PurchaseOrderListPage,
      }),
    },
    {
      path: appRoutes.procurement.purchaseOrderNew,
      lazy: async () => ({
        Component: (await import('./pages/purchase-order-detail-page'))
          .PurchaseOrderDetailPage,
      }),
    },
    {
      path: appRoutes.procurement.purchaseOrderDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/purchase-order-detail-page'))
          .PurchaseOrderDetailPage,
      }),
    },
    {
      path: appRoutes.procurement.purchaseProgress,
      lazy: async () => ({
        Component: (await import('./pages/purchase-progress-page')).PurchaseProgressPage,
      }),
    },
    {
      path: appRoutes.procurement.surveys,
      lazy: async () => ({
        Component: (await import('./pages/survey-list-page')).SurveyListPage,
      }),
    },
    {
      path: appRoutes.procurement.surveyNew,
      lazy: async () => ({
        Component: (await import('./pages/survey-detail-page')).SurveyDetailPage,
      }),
    },
    {
      path: appRoutes.procurement.surveyDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/survey-detail-page')).SurveyDetailPage,
      }),
    },
    {
      path: appRoutes.procurement.surveyReport,
      lazy: async () => ({
        Component: (await import('./pages/survey-report-page')).SurveyReportPage,
      }),
    },
    {
      path: appRoutes.procurement.purchaseReport,
      lazy: async () => ({
        Component: (await import('./pages/purchase-report-page')).PurchaseReportPage,
      }),
    },
    {
      path: appRoutes.procurement.categoryAssignees,
      lazy: async () => ({
        Component: (await import('./pages/category-assignee-list-page')).CategoryAssigneeListPage,
      }),
    },
    {
      path: appRoutes.procurement.categoryAssigneeNew,
      lazy: async () => ({
        Component: (await import('./pages/category-assignee-form-page')).CategoryAssigneeFormPage,
      }),
    },
  ],
}
