import { LayoutDashboard, Wallet } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

/** Phân hệ TÀI CHÍNH — mới đăng ký chỗ, chưa có chức năng. */
export const financeModule: ErpModule = {
  id: 'finance',
  title: 'Tài chính',
  description: 'Công nợ, đề nghị thanh toán và chi phí.',
  icon: Wallet,
  path: appRoutes.finance.root,
  accent: 'bg-violet-50 text-violet-600',
  enabled: false,
  entity: 'payment',

  nav: [
    {
      label: 'Tổng quan',
      path: appRoutes.finance.root,
      icon: LayoutDashboard,
      end: true,
    },
  ],

  routes: [
    {
      path: appRoutes.finance.root,
      lazy: async () => ({
        Component: (await import('./pages/finance-dashboard-page')).FinanceDashboardPage,
      }),
    },
  ],
}
