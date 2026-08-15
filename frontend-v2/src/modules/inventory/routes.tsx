import { Boxes, LayoutDashboard } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

/** Phân hệ KHO — mới đăng ký chỗ, chưa có chức năng. */
export const inventoryModule: ErpModule = {
  id: 'inventory',
  title: 'Kho',
  description: 'Tồn kho, nhập xuất và luân chuyển kho.',
  icon: Boxes,
  path: appRoutes.inventory.root,
  accent: 'bg-amber-50 text-amber-600',
  enabled: false,
  entity: 'inventory',

  nav: [
    {
      label: 'Tổng quan',
      path: appRoutes.inventory.root,
      icon: LayoutDashboard,
      end: true,
    },
  ],

  routes: [
    {
      path: appRoutes.inventory.root,
      lazy: async () => ({
        Component: (await import('./pages/inventory-dashboard-page'))
          .InventoryDashboardPage,
      }),
    },
  ],
}
