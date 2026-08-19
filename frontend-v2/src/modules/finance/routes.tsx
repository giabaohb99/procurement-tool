import { LayoutDashboard, ReceiptText, Wallet } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Phân hệ TÀI CHÍNH.
 *
 * Mới có Công nợ phải trả. Yêu cầu thanh toán (kèm phiếu in) là màn tiếp theo
 * của phân hệ này — cho tới lúc đó, chỗ tick chọn khoản nợ để lên đề nghị thanh
 * toán vẫn nằm ở bản `frontend` cũ.
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
  ],
}
