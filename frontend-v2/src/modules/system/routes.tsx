import { LayoutDashboard, Settings, SlidersHorizontal } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Phân hệ QUẢN TRỊ HỆ THỐNG.
 *
 * Hiện mới có Cấu hình hệ thống. Sao lưu CSDL và Quản lý Import sẽ vào đúng
 * menu này khi làm xong — chưa khai ở `nav` vì mục menu trỏ vào màn chưa tồn
 * tại thì bấm ra trang 404.
 *
 * Phân quyền tài khoản KHÔNG nằm ở đây mà ở phân hệ Nhân sự: dữ liệu gốc của
 * nó là nhân sự và tài khoản. Trang tổng quan có lối tắt sang.
 */
export const systemModule: ErpModule = {
  id: 'system',
  // Nhãn ngắn để không xuống dòng trong ô 112px; mô tả bên dưới nói rõ phạm vi.
  title: 'Quản trị',
  description: 'Cấu hình hệ thống, sao lưu và các tác vụ quản trị.',
  icon: Settings,
  path: appRoutes.system.root,
  accent: 'bg-slate-100 text-slate-600',
  enabled: true,
  entity: 'setting',

  nav: [
    { label: 'Tổng quan', path: appRoutes.system.root, icon: LayoutDashboard, end: true },
    {
      label: 'Cấu hình hệ thống',
      path: appRoutes.system.settings,
      icon: SlidersHorizontal,
      entity: 'setting',
    },
  ],

  routes: [
    {
      path: appRoutes.system.root,
      lazy: async () => ({
        Component: (await import('./pages/system-dashboard-page')).SystemDashboardPage,
      }),
    },
    {
      path: appRoutes.system.settings,
      lazy: async () => ({
        Component: (await import('./pages/setting-page')).SettingPage,
      }),
    },
  ],
}
