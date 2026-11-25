import {
  BarChart3,
  ChartColumnBig,
  ChartLine,
  ClipboardCheck,
  ClipboardList,
  Coins,
  FileStack,
  FileText,
  History,
  Landmark,
  LayoutDashboard,
  List,
  ListTree,
  PackagePlus,
  ReceiptText,
  ShoppingCart,
  Sigma,
  Tags,
  TextSearch,
  TrendingUp,
  Truck,
  UserCheck,
  WalletCards,
} from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import {
  PurchaseOrderPendingNavBadge,
  PurchaseRequestPendingNavBadge,
  SurveyPendingNavBadge,
  SurveyRequestPendingNavBadge,
} from './components/procurement-pending-nav-badge'
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
    // nhóm Mua hàng xếp YCBG → Tiến độ báo giá → YCMH → ĐMH → Tiến độ đơn mua hàng
    // → Chi tiết YC mua hàng (bao-CR-691).
    {
      label: 'Báo cáo mua hàng',
      path: appRoutes.procurement.purchaseReport,
      icon: ChartColumnBig,
      entity: 'report',
    },
    {
      label: 'Yêu cầu báo giá',
      path: appRoutes.procurement.surveyRequests,
      icon: ClipboardList,
      entity: 'survey_request',
      badge: SurveyRequestPendingNavBadge,
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
      badge: PurchaseRequestPendingNavBadge,
      group: 'Mua hàng',
    },
    {
      label: 'Đơn mua hàng',
      path: appRoutes.procurement.purchaseOrders,
      icon: ShoppingCart,
      entity: 'purchase_order',
      badge: PurchaseOrderPendingNavBadge,
      group: 'Mua hàng',
    },
    {
      label: 'Tiến độ đơn mua hàng',
      path: appRoutes.procurement.purchaseProgress,
      icon: Truck,
      entity: 'purchase_request',
      group: 'Mua hàng',
    },
    // bao-CR-296/299 — trang riêng của tab "Chi tiết YC mua hàng" (entity `report`
    // như menu v1). bao-CR-691 (đại ca chốt 28/10): dời từ đầu menu xuống nhóm
    // Mua hàng, đứng NGAY SAU Tiến độ đơn mua hàng — hai báo cáo theo dõi cùng
    // một chuỗi (dòng YCMH → dòng ĐMH → lần giao) nên đặt cạnh nhau.
    // bao-CR-739: mở cho người có `report` HOẶC `purchase_request` (đọc) — người chỉ
    // có Xem YCMH thấy đúng dòng trong phạm vi YCMH của mình (máy chủ lọc).
    {
      label: 'Chi tiết YC mua hàng',
      path: appRoutes.procurement.prLinesReport,
      icon: TextSearch,
      entities: ['report', 'purchase_request'],
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
          //  bao-CR-718: thêm "Lô xuất của tôi" (+ chi tiết lô) — lô sinh từ thẻ Danh sách nên mục này sáng.
          matchPaths: [
            ...CUSTOMS_TAB_SECTIONS.filter((section) => section.key !== 'list').map((section) =>
              buildCustomsSectionPath(section.key),
            ),
            appRoutes.procurement.customsExports,
          ],
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
          //  "Cấu hình": quản lý `customs_price` (từ khóa + đồng nghĩa) HOẶC đọc
          //  `customs_regulation` (danh mục hóa chất) — cùng luật `showConfigTab` của trang.
          ...(section.key === 'config' && {
            manage: true,
            alsoReadable: ['customs_regulation' as const],
          }),
        })),
        //  bao-CR-718 — "Lô xuất của tôi" + chi tiết lô: mục ẨN (vào từ menu nút Xuất dữ liệu / chuông),
        //  khai riêng để `canAccessRoute` đòi `customs_price.export` thay vì quyền đọc của mục cha. Mục
        //  "Giá thị trường" trỏ tới nó qua `matchPaths` (luật mục ẩn) — breadcrumb: Tra cứu thị trường › Giá thị trường.
        {
          label: 'Lô xuất của tôi',
          path: appRoutes.procurement.customsExports,
          icon: FileStack,
          entity: 'customs_price' as const,
          action: 'export' as const,
          hidden: true,
        },
      ],
    },
    //  duoc-CR-784 — cụm Giá nguyên vật liệu sản xuất (tên chốt 21/11/2026, trước là Giá bao bì), khóa RIÊNG `packaging_cost`
    //  (giá vốn bao bì, nhạy cảm). 25/11/2026 (người chủ chốt): vẽ như "Tra cứu thị trường" — MỘT mục cha có biểu tượng,
    //  mục con thụt vào có vạch dọc. Mục cha KHÔNG khai `group` và đứng sau nhóm Mua hàng nên thanh bên vẽ nó thành một
    //  khối không tiêu đề ngay tại chỗ (xem `app/layouts/build-nav-sections.ts`) — vẫn tách khỏi Mua hàng.
    //  Mục con Tác động ở đường gốc của cụm nên phải `end: true`, không thì nó sáng lây khi đứng ở các mục con khác.
    {
      label: 'Giá nguyên vật liệu sản xuất',
      path: appRoutes.procurement.packagingImpact,
      icon: Coins,
      entity: 'packaging_cost',
      children: [
        {
          label: 'Tác động giá bao bì',
          path: appRoutes.procurement.packagingImpact,
          icon: TrendingUp,
          entity: 'packaging_cost',
          end: true,
        },
        {
          label: 'Tổng hợp theo sản phẩm',
          path: appRoutes.procurement.packagingProducts,
          icon: Sigma,
          entity: 'packaging_cost',
        },
        {
          label: 'Bảng giá VTBB',
          path: appRoutes.procurement.packagingPrices,
          icon: WalletCards,
          entity: 'packaging_cost',
          //  Màn Báo giá VTBB (ẩn khỏi menu) thuộc về đây: báo giá nhập từ Bảng giá, đứng ở màn đó thì sáng mục này.
          matchPaths: [appRoutes.procurement.packagingQuotes],
        },
        {
          label: 'Giá mua gần nhất',
          path: appRoutes.procurement.packagingLastPrices,
          icon: History,
          entity: 'packaging_cost',
        },
        {
          label: 'Lịch sử mua hàng',
          path: appRoutes.procurement.packagingHistory,
          icon: ChartLine,
          entity: 'packaging_cost',
        },
        {
          label: 'Báo giá VTBB',
          path: appRoutes.procurement.packagingQuotes,
          icon: Tags,
          entity: 'packaging_cost',
          //  Ẩn khỏi menu (người chủ chốt 21/11/2026: file HTML gốc không có tab này, báo giá nhập ngay ở Bảng giá VTBB).
          //  Giữ mục để đường dẫn vẫn bị gác quyền packaging_cost — bỏ hẳn mục là route mở cho mọi người đăng nhập.
          hidden: true,
        },
        {
          label: 'Định mức bao bì',
          path: appRoutes.procurement.packagingBoms,
          icon: ListTree,
          entity: 'packaging_cost',
        },
      ],
    },
    {
      label: 'Phiếu khảo sát',
      path: appRoutes.procurement.surveys,
      icon: ClipboardCheck,
      entity: 'survey',
      badge: SurveyPendingNavBadge,
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
    // khóa nhãn + từ đồng nghĩa (bao-CR-494 / 495) — đã dời vào thẻ "Cấu hình" của chính màn
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
    // duoc-CR-784 — cụm Giá bao bì
    {
      path: appRoutes.procurement.packagingImpact,
      lazy: async () => ({
        Component: (await import('./pages/packaging-impact-page')).PackagingImpactPage,
      }),
    },
    {
      path: appRoutes.procurement.packagingProducts,
      lazy: async () => ({
        Component: (await import('./pages/packaging-product-overview-page'))
          .PackagingProductOverviewPage,
      }),
    },
    {
      path: appRoutes.procurement.packagingPrices,
      lazy: async () => ({
        Component: (await import('./pages/packaging-price-list-page')).PackagingPriceListPage,
      }),
    },
    {
      path: appRoutes.procurement.packagingLastPrices,
      lazy: async () => ({
        Component: (await import('./pages/packaging-last-prices-page')).PackagingLastPricesPage,
      }),
    },
    {
      path: appRoutes.procurement.packagingHistory,
      lazy: async () => ({
        Component: (await import('./pages/packaging-history-page')).PackagingHistoryPage,
      }),
    },
    {
      path: appRoutes.procurement.packagingQuotes,
      lazy: async () => ({
        Component: (await import('./pages/packaging-quote-list-page')).PackagingQuoteListPage,
      }),
    },
    {
      path: appRoutes.procurement.packagingBoms,
      lazy: async () => ({
        Component: (await import('./pages/packaging-bom-list-page')).PackagingBomListPage,
      }),
    },
    // bao-CR-470 — Tra cứu thị trường (danh mục hóa chất nằm trong thẻ "Cấu hình", bao-CR-501)
    {
      path: appRoutes.procurement.customsPrices,
      lazy: async () => ({
        Component: (await import('./pages/customs-price-page')).CustomsPricePage,
      }),
    },
    //  duoc-CR-492 — chi tiết một thuốc BVTV. Nằm DƯỚI đường mục "Thuốc BVTV" nên `canAccessRoute`
    //  gác bằng chính mục menu đó (`customs_price.read`), không mở cửa riêng.
    {
      path: appRoutes.procurement.customsPesticideDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/customs-pesticide-detail-page')).CustomsPesticideDetailPage,
      }),
    },
    //  bao-CR-718 — lô xuất toàn bộ chạy nền. Đường TĨNH `exports` khai TRƯỚC `:section` (router v7 vẫn xếp
    //  đường tĩnh thắng, khai trước cho người đọc khỏi nghi); `exports` không phải khóa của `CUSTOMS_SECTIONS`
    //  nên trang Tra cứu không bao giờ tự chuyển hướng nó.
    {
      path: appRoutes.procurement.customsExports,
      lazy: async () => ({
        Component: (await import('./pages/customs-export-list-page')).CustomsExportListPage,
      }),
    },
    {
      path: appRoutes.procurement.customsExportDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/customs-export-detail-page')).CustomsExportDetailPage,
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
