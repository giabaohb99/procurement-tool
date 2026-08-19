import { Boxes, LayoutDashboard, Warehouse } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Phân hệ KHO.
 *
 * Mới có Tồn kho. Nhập xuất và luân chuyển kho vẫn nằm ở bản `frontend` cũ.
 */
export const inventoryModule: ErpModule = {
  id: 'inventory',
  title: 'Kho',
  description: 'Tồn kho, nhập xuất và luân chuyển kho.',
  icon: Boxes,
  path: appRoutes.inventory.root,
  accent: 'bg-amber-50 text-amber-600',
  enabled: true,
  entity: 'inventory',

  nav: [
    {
      label: 'Tổng quan',
      path: appRoutes.inventory.root,
      icon: LayoutDashboard,
      end: true,
    },
    {
      label: 'Tồn kho',
      path: appRoutes.inventory.stock,
      icon: Warehouse,
      entity: 'inventory',
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
    {
      path: appRoutes.inventory.stock,
      lazy: async () => ({
        Component: (await import('./pages/inventory-list-page')).InventoryListPage,
      }),
    },
  ],
}
