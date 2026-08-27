import { LayoutDashboard, Receipt } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

/** Phân hệ BÁN HÀNG — mới đăng ký chỗ, chưa có chức năng. */
export const salesModule: ErpModule = {
  id: 'sales',
  title: 'Bán hàng',
  description: 'Đơn hàng, khách hàng và doanh thu.',
  icon: Receipt,
  path: appRoutes.sales.root,
  accent: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
  enabled: false,

  nav: [
    { label: 'Tổng quan', path: appRoutes.sales.root, icon: LayoutDashboard, end: true },
  ],

  routes: [
    {
      path: appRoutes.sales.root,
      lazy: async () => ({
        Component: (await import('./pages/sales-dashboard-page')).SalesDashboardPage,
      }),
    },
  ],
}
