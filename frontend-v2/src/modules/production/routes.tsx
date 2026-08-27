import { Factory, FileText, Layers, LayoutDashboard, Package, Ruler, Users } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Phân hệ SẢN XUẤT.
 *
 * Quản lý danh mục Nhà cung cấp, Sản phẩm & VTBB, Đơn vị tính,
 * Phân loại VTBB/NL và Hợp đồng dùng chung cho toàn hệ thống.
 */
export const productionModule: ErpModule = {
  id: 'production',
  title: 'Sản xuất',
  description: 'Lệnh sản xuất, định mức nguyên liệu và tiến độ.',
  icon: Factory,
  path: appRoutes.production.root,
  accent: 'bg-teal-500/10 text-teal-600 dark:text-teal-400',
  enabled: true,

  nav: [
    {
      label: 'Tổng quan',
      path: appRoutes.production.root,
      icon: LayoutDashboard,
      end: true,
      // Không có quyền đọc khóa nào của phân hệ thì ẩn luôn Tổng quan —
      // cùng luật với Thu mua, xem procurement/routes.tsx.
      entities: ['supplier', 'product', 'unit', 'item_group', 'contract'],
    },
    {
      label: 'Nhà cung cấp',
      path: appRoutes.production.suppliers,
      icon: Users,
      entity: 'supplier',
      group: 'Danh mục',
    },
    {
      label: 'Sản phẩm & Vật tư',
      path: appRoutes.production.products,
      icon: Package,
      entity: 'product',
      group: 'Danh mục',
    },
    {
      label: 'Đơn vị tính',
      path: appRoutes.production.units,
      icon: Ruler,
      entity: 'unit',
      group: 'Danh mục',
    },
    {
      label: 'Phân loại VTBB',
      path: appRoutes.production.itemGroups,
      icon: Layers,
      entity: 'item_group',
      group: 'Danh mục',
    },
    {
      label: 'Hợp đồng',
      path: appRoutes.production.contracts,
      icon: FileText,
      entity: 'contract',
      group: 'Danh mục',
    },
  ],

  routes: [
    {
      path: appRoutes.production.root,
      lazy: async () => ({
        Component: (await import('./pages/production-dashboard-page'))
          .ProductionDashboardPage,
      }),
    },
    {
      path: appRoutes.production.suppliers,
      lazy: async () => ({
        Component: (await import('./pages/supplier-list-page')).SupplierListPage,
      }),
    },
    {
      path: `${appRoutes.production.suppliers}/:id`,
      lazy: async () => ({
        Component: (await import('./pages/supplier-detail-page')).SupplierDetailPage,
      }),
    },
    {
      path: appRoutes.production.products,
      lazy: async () => ({
        Component: (await import('./pages/product-list-page')).ProductListPage,
      }),
    },
    {
      path: `${appRoutes.production.products}/:id`,
      lazy: async () => ({
        Component: (await import('./pages/product-detail-page')).ProductDetailPage,
      }),
    },
    {
      path: appRoutes.production.units,
      lazy: async () => ({
        Component: (await import('./pages/unit-list-page')).UnitListPage,
      }),
    },
    {
      path: `${appRoutes.production.units}/:id`,
      lazy: async () => ({
        Component: (await import('./pages/unit-detail-page')).UnitDetailPage,
      }),
    },
    {
      path: appRoutes.production.itemGroups,
      lazy: async () => ({
        Component: (await import('./pages/item-group-list-page')).ItemGroupListPage,
      }),
    },
    {
      path: `${appRoutes.production.itemGroups}/:id`,
      lazy: async () => ({
        Component: (await import('./pages/item-group-detail-page')).ItemGroupDetailPage,
      }),
    },
    {
      path: appRoutes.production.contracts,
      lazy: async () => ({
        Component: (await import('./pages/contract-list-page')).ContractListPage,
      }),
    },
    {
      path: `${appRoutes.production.contracts}/:id`,
      lazy: async () => ({
        Component: (await import('./pages/contract-detail-page')).ContractDetailPage,
      }),
    },
  ],
}
