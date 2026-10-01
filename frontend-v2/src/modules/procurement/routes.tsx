import {
  BarChart3,
  ChartColumnBig,
  ClipboardCheck,
  ClipboardList,
  FileText,
  Landmark,
  LayoutDashboard,
  List,
  PackagePlus,
  ReceiptText,
  ShoppingCart,
  TextSearch,
  Truck,
  UserCheck,
} from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

import {
  buildCustomsSectionPath,
  CUSTOMS_SECTIONS,
  CUSTOMS_TAB_GROUP_LABEL,
  CUSTOMS_TAB_SECTIONS,
} from './config/customs-sections'

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
    // bao-CR-296/299 — trang riêng của tab "Chi tiết YC mua hàng", đứng ngay
    // dưới Báo cáo mua hàng như bản v1 (entity `report` như menu v1).
    {
      label: 'Chi tiết YC mua hàng',
      path: appRoutes.procurement.prLinesReport,
      icon: TextSearch,
      entity: 'report',
    },
    {
      label: 'Yêu cầu báo giá',
      path: appRoutes.procurement.surveyRequests,
      icon: ClipboardList,
      entity: 'survey_request',
      group: 'Mua hàng',
    },
    {
      label: 'Tiến độ báo giá',
      path: appRoutes.procurement.surveyProgress,
      icon: Truck,
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
    // bao-CR-470 — Tra cứu giá hải quan, khóa riêng `customs_price`. Bộ lọc dùng chung trên URL nên
    // `keepSearch`. 01/10/2026: năm mục tra giá (Danh sách · Biểu đồ · Nhà nhập khẩu · So sánh ·
    // Thuế) gom về MỘT mục con — chuyển bằng thẻ trên đầu trang; các mục khác vẫn là submenu.
    {
      label: 'Tra cứu thị trường',
      path: appRoutes.procurement.customsPrices,
      icon: Landmark,
      entity: 'customs_price',
      group: 'Mua hàng',
      keepSearch: true,
      children: [
        {
          label: CUSTOMS_TAB_GROUP_LABEL,
          path: appRoutes.procurement.customsPrices,
          icon: List,
          entity: 'customs_price' as const,
          //  Mục ở đường gốc — không `end` thì nó sáng lây ở mọi mục con; bốn thẻ còn lại
          //  có đường riêng nên khai `matchPaths` để mục vẫn sáng khi đang đứng ở thẻ đó.
          end: true,
          matchPaths: CUSTOMS_TAB_SECTIONS.filter((section) => section.key !== 'list').map(
            (section) => buildCustomsSectionPath(section.key),
          ),
        },
        //  Bốn thẻ còn lại: mục ẨN — không vẽ trên menu, nhưng giữ khóa quyền của chính nó
        //  cho `canAccessRoute` và là đích của `matchPaths` phía trên (luật `hidden`).
        ...CUSTOMS_TAB_SECTIONS.filter((section) => section.key !== 'list').map((section) => ({
          label: section.label,
          path: buildCustomsSectionPath(section.key),
          icon: section.icon,
          entity: 'customs_price' as const,
          hidden: true,
        })),
        ...CUSTOMS_SECTIONS.filter((section) => !section.tabbed).map((section) => ({
          label: section.label,
          path: buildCustomsSectionPath(section.key),
          icon: section.icon,
          entity: 'customs_price' as const,
          //  «Cấu hình»: quản lý `customs_price` (từ khóa + đồng nghĩa) HOẶC đọc
          //  `customs_regulation` (danh mục hóa chất) — cùng luật `showConfigTab` của trang.
          ...(section.key === 'config' && {
            manage: true,
            alsoReadable: ['customs_regulation' as const],
          }),
        })),
      ],
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
    // bao-CR-453 — danh mục loại chi phí thu mua
    {
      label: 'Loại chi phí thu mua',
      path: appRoutes.procurement.poCostTypes,
      icon: PackagePlus,
      entity: 'purchase_cost_type',
      manage: true,
      group: 'Cấu hình',
    },
    // bao-CR-501: ba danh mục của Tra cứu thị trường — hóa chất theo văn bản (bao-CR-470), từ
    // khóa nhãn + từ đồng nghĩa (bao-CR-494 / 495) — đã dời vào thẻ «Cấu hình» của chính màn
    // đó, không còn mục menu / màn riêng.
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
      // bao-CR-310 — màn Xử lý phương án của YCMH, tách trang như màn xử lý YCBG.
      path: appRoutes.procurement.purchaseRequestProcess(':id'),
      lazy: async () => ({
        Component: (await import('./pages/purchase-request-process-page'))
          .PurchaseRequestProcessPage,
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
      path: appRoutes.procurement.surveyProgress,
      lazy: async () => ({
        Component: (await import('./pages/survey-progress-page')).SurveyProgressPage,
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
      path: appRoutes.procurement.prLinesReport,
      lazy: async () => ({
        Component: (await import('./pages/pr-lines-report-page')).PrLinesReportPage,
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
    // bao-CR-453 — danh mục loại chi phí thu mua
    {
      path: appRoutes.procurement.poCostTypes,
      lazy: async () => ({
        Component: (await import('./pages/po-cost-type-list-page')).PoCostTypeListPage,
      }),
    },
    {
      path: appRoutes.procurement.poCostTypeDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/po-cost-type-detail-page')).PoCostTypeDetailPage,
      }),
    },
    // bao-CR-470 — Tra cứu thị trường (danh mục hóa chất nằm trong thẻ «Cấu hình», bao-CR-501)
    {
      path: appRoutes.procurement.customsPrices,
      lazy: async () => ({
        Component: (await import('./pages/customs-price-page')).CustomsPricePage,
      }),
    },
    //  duoc-CR-492 — chi tiết một thuốc BVTV. Nằm DƯỚI đường mục «Thuốc BVTV» nên `canAccessRoute`
    //  gác bằng chính mục menu đó (`customs_price.read`), không mở cửa riêng.
    {
      path: appRoutes.procurement.customsPesticideDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/customs-pesticide-detail-page')).CustomsPesticideDetailPage,
      }),
    },
    {
      path: appRoutes.procurement.customsPriceSection(':section'),
      lazy: async () => ({
        Component: (await import('./pages/customs-price-page')).CustomsPricePage,
      }),
    },
  ],
}
