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
  accent: 'bg-amber-500/10 text-amber-600 dark:text-amber-400',
  enabled: true,
  entity: 'inventory',

  nav: [
    {
      label: 'Tổng quan',
      path: appRoutes.inventory.root,
      icon: LayoutDashboard,
      end: true,
      //  ⚠️ ĐÚNG MỘT KHÓA `inventory` (bao-CR-380, 11/09/2026). Trước đó mục này
      //  khai `entities: ['inventory', 'warehouse']` — hiện khi có BẤT KỲ khóa
      //  nào — trong khi trang Tổng quan bên trong lại đòi đúng `inventory.read`.
      //  Hai luật lệch nhau nên người chỉ có `warehouse.read` được menu mời vào
      //  rồi trang đóng cửa bằng một ô đỏ; khách bắt đúng ca này trên dev.
      //  Trang nói về SỐ LIỆU TỒN KHO, nên khóa của nó là `inventory`. Người chỉ
      //  giữ danh mục kho không mất gì: `ModuleLayout` đẩy họ thẳng tới *Danh mục
      //  Kho* — xem `firstAccessibleNavPath`.
      entity: 'inventory',
    },
    {
      label: 'Tồn kho',
      path: appRoutes.inventory.stock,
      icon: Warehouse,
      entity: 'inventory',
    },
    {
      label: 'Danh mục Kho',
      path: appRoutes.inventory.warehouses,
      icon: Warehouse,
      entity: 'warehouse',
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
    {
      path: appRoutes.inventory.warehouses,
      lazy: async () => ({
        Component: (await import('./pages/warehouse-list-page')).WarehouseListPage,
      }),
    },
    {
      path: `${appRoutes.inventory.warehouses}/:id`,
      lazy: async () => ({
        Component: (await import('./pages/warehouse-detail-page')).WarehouseDetailPage,
      }),
    },
  ],
}
