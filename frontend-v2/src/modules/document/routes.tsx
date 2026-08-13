import { FileText, LayoutDashboard } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Phân hệ VĂN BẢN — mới dựng khung ở frontend.
 * Nơi quản lý công văn, quyết định, hợp đồng và biểu mẫu nội bộ.
 *
 * ⚠️ Backend CHƯA có gì cho phân hệ này: chưa có endpoint và `ENTITIES` trong
 * `core/permissions.py` chưa có `document`. Vì vậy chưa gắn được `entity` để lọc
 * quyền — hiện tại ai đăng nhập cũng thấy phân hệ này. Khi backend thêm entity
 * thì bổ sung vào đây để siết lại.
 */
export const documentModule: ErpModule = {
  id: 'document',
  title: 'Văn bản',
  description: 'Công văn, quyết định, hợp đồng và biểu mẫu nội bộ.',
  icon: FileText,
  path: appRoutes.document.root,
  accent: 'bg-indigo-50 text-indigo-600',
  enabled: true,

  nav: [
    {
      label: 'Tổng quan',
      path: appRoutes.document.root,
      icon: LayoutDashboard,
      end: true,
    },
  ],

  routes: [
    {
      path: appRoutes.document.root,
      lazy: async () => ({
        Component: (await import('./pages/document-dashboard-page'))
          .DocumentDashboardPage,
      }),
    },
  ],
}
