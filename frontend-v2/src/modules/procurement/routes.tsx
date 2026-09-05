import {
  BarChart3,
  ChartColumnBig,
  ClipboardCheck,
  ClipboardList,
  FileText,
  LayoutDashboard,
  ReceiptText,
  ShoppingCart,
  Truck,
  UserCheck,
} from 'lucide-react'
import { Navigate } from 'react-router-dom'

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
      // Không có quyền đọc khóa nào của phân hệ thì Tổng quan cũng không có gì
      // để vẽ (dashboard gác từng khối bằng can(entity)) — ẩn luôn, kẻo tài
      // khoản ngoài phân hệ (vd văn thư) thấy thẻ Thu mua mở mà vào toàn số 0.
      entities: ['survey_request', 'purchase_request', 'purchase_order', 'survey', 'report'],
    },
    // Thứ tự menu bám theo bản v1 (`frontend/src/layouts/AppLayout.tsx`) — khách
    // chốt 29/08 "sửa lại như bản cũ": Báo cáo mua hàng đứng riêng đầu menu,
    // nhóm Mua hàng xếp YCBG → Tiến độ báo giá → YCMH → ĐMH → Tiến độ mua hàng.
    {
      label: 'Báo cáo mua hàng',
      path: appRoutes.procurement.purchaseReport,
      icon: ChartColumnBig,
      entity: 'report',
    },
    // bao-CR-288: chạy thử luồng gộp P6 — YCBG đứng tên "Yêu cầu mua hàng" (nó
    // chính là phiếu yêu cầu của luồng mới), mục YCMH cũ ẨN TẠM khỏi menu. Route
    // /procurement/purchase-requests vẫn đăng ký để phiếu YCMH cũ mở từ link /
    // thông báo còn đọc được. Khách chốt bỏ hẳn thì mới gỡ route + càn quét nhãn.
    {
      label: 'Yêu cầu mua hàng',
      path: appRoutes.procurement.surveyRequests,
      icon: ClipboardList,
      entity: 'survey_request',
      group: 'Mua hàng',
    },
    // P6-6 (bao-CR-284): mục "Tiến độ báo giá" đã gộp vào "Tiến độ mua hàng"
    // (bước "Đang so giá") — xem đính chính doc/erp/12 §2.7.
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
    // Hai lối tắt sang phân hệ TÀI CHÍNH (`crossModule`) — màn hình vẫn là của
    // Tài chính, đây chỉ là đường dẫn phụ. Người mua hàng tra công nợ rồi lên đề
    // nghị thanh toán hằng ngày, bắt vòng qua màn chọn phân hệ là thừa hai cú
    // bấm (khách yêu cầu 31/08/2026). Nhãn và icon giữ y hệt bên Tài chính để
    // vào rồi không thấy lạc.
    {
      label: 'Công nợ phải trả',
      path: appRoutes.finance.payables,
      icon: ReceiptText,
      entity: 'payable',
      crossModule: true,
      group: 'Tài chính',
    },
    {
      label: 'Yêu cầu thanh toán',
      path: appRoutes.finance.paymentRequests,
      icon: FileText,
      entity: 'payment_request',
      crossModule: true,
      group: 'Tài chính',
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
      path: appRoutes.procurement.surveyRequestProcess(':id'),
      lazy: async () => ({
        Component: (await import('./pages/survey-request-process-page'))
          .SurveyRequestProcessPage,
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
      path: appRoutes.procurement.purchaseOrderDocuments(':id'),
      lazy: async () => ({
        Component: (await import('./pages/purchase-order-document-chain-page'))
          .PurchaseOrderDocumentChainPage,
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
      // P6-6 (bao-CR-284): màn Tiến độ báo giá đã gộp vào Tiến độ mua hàng —
      // đường dẫn cũ (bookmark, link trong thông báo) đưa thẳng về bước So giá.
      path: appRoutes.procurement.surveyProgress,
      element: (
        <Navigate to={`${appRoutes.procurement.purchaseProgress}?step=quoting`} replace />
      ),
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
