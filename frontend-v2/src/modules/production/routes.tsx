import { Factory, LayoutDashboard, Users } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Phân hệ SẢN XUẤT — mới dựng khung ở frontend.
 *
 * ⚠️ Backend CHƯA có gì cho phân hệ này: chưa có `app/modules/production/`, chưa
 * có endpoint, và `ENTITIES` trong `core/permissions.py` chưa có `production`.
 * Vì vậy chưa gắn được `entity` để lọc quyền — hiện tại ai đăng nhập cũng thấy
 * phân hệ này. Khi backend thêm entity thì bổ sung vào đây để siết lại.
 */
export const productionModule: ErpModule = {
  id: 'production',
  title: 'Sản xuất',
  description: 'Lệnh sản xuất, định mức nguyên liệu và tiến độ.',
  icon: Factory,
  path: appRoutes.production.root,
  accent: 'bg-teal-50 text-teal-600',
  enabled: true,

  nav: [
    {
      label: 'Tổng quan',
      path: appRoutes.production.root,
      icon: LayoutDashboard,
      end: true,
    },
    {
      // Danh mục NCC / đơn vị vận chuyển do Sản xuất quản lý, Thu mua chỉ dùng
      // lại dữ liệu (cột "Nhà cung cấp" ở đơn mua hàng, tiến độ…).
      label: 'Nhà cung cấp',
      path: appRoutes.production.suppliers,
      icon: Users,
      entity: 'supplier',
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
  ],
}
