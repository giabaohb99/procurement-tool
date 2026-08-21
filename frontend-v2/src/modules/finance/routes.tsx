import { FileText, LayoutDashboard, ReceiptText, Wallet } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Phân hệ TÀI CHÍNH.
 *
 * Gồm Công nợ phải trả và Yêu cầu thanh toán (danh sách + chi tiết; bản in đăng
 * ký ngoài khung phân hệ ở `app-router.tsx`). Lối chính để lên phiếu là cột tick
 * ở màn Công nợ; nút ở màn danh sách YCTT là lối phụ cho khoản chi không đi từ
 * công nợ (form trắng, CR-066).
 */
export const financeModule: ErpModule = {
  id: 'finance',
  title: 'Tài chính',
  description: 'Công nợ, đề nghị thanh toán và chi phí.',
  icon: Wallet,
  path: appRoutes.finance.root,
  accent: 'bg-violet-50 text-violet-600',
  enabled: true,
  // KHÔNG khai `entity` ở tầng module (trước để `payment`): người chỉ có
  // `payable.read` — xem công nợ nhưng không được lập đề nghị thanh toán — sẽ
  // không thấy phân hệ. Chặn theo TỪNG mục menu bên dưới mới đúng.

  nav: [
    {
      label: 'Tổng quan',
      path: appRoutes.finance.root,
      icon: LayoutDashboard,
      end: true,
    },
    {
      label: 'Công nợ phải trả',
      path: appRoutes.finance.payables,
      icon: ReceiptText,
      entity: 'payable',
    },
    {
      label: 'Yêu cầu thanh toán',
      path: appRoutes.finance.paymentRequests,
      icon: FileText,
      entity: 'payment_request',
    },
  ],

  routes: [
    {
      path: appRoutes.finance.root,
      lazy: async () => ({
        Component: (await import('./pages/finance-dashboard-page')).FinanceDashboardPage,
      }),
    },
    {
      path: appRoutes.finance.payables,
      lazy: async () => ({
        Component: (await import('./pages/payable-list-page')).PayableListPage,
      }),
    },
    {
      path: appRoutes.finance.paymentRequests,
      lazy: async () => ({
        Component: (await import('./pages/payment-request-list-page')).PaymentRequestListPage,
      }),
    },
    // `/new` khai TRƯỚC `:id` để đường dẫn tạo mới không rơi vào nhánh tham số.
    {
      path: appRoutes.finance.paymentRequestNew,
      lazy: async () => ({
        Component: (await import('./pages/payment-request-detail-page')).PaymentRequestDetailPage,
      }),
    },
    {
      path: appRoutes.finance.paymentRequestDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/payment-request-detail-page')).PaymentRequestDetailPage,
      }),
    },
  ],
}
