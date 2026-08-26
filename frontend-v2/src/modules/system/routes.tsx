import { AtSign, Database, History, LayoutDashboard, Settings, SlidersHorizontal } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Phân hệ QUẢN TRỊ HỆ THỐNG.
 *
 * Quản lý cấu hình hệ thống, sao lưu CSDL, nhật ký hệ thống và các tác vụ quản trị.
 * Phân quyền tài khoản KHÔNG nằm ở đây mà ở phân hệ Nhân sự.
 */
export const systemModule: ErpModule = {
  id: 'system',
  // Nhãn ngắn để không xuống dòng trong ô 112px; mô tả bên dưới nói rõ phạm vi.
  title: 'Quản trị',
  description: 'Cấu hình hệ thống, sao lưu CSDL và các tác vụ quản trị.',
  icon: Settings,
  path: appRoutes.system.root,
  accent: 'bg-slate-100 text-slate-600',
  enabled: true,
  entity: 'setting',

  nav: [
    {
      label: 'Tổng quan',
      path: appRoutes.system.root,
      icon: LayoutDashboard,
      end: true,
      entity: 'setting',
      manage: true,
    },
    {
      label: 'Cấu hình hệ thống',
      path: appRoutes.system.settings,
      icon: SlidersHorizontal,
      entity: 'setting',
      manage: true,
    },
    {
      label: 'Sao lưu CSDL',
      path: appRoutes.system.backups,
      icon: Database,
      entity: 'backup',
      manage: true,
    },
    {
      label: 'Hộp thư gửi',
      path: appRoutes.system.mailboxes,
      icon: AtSign,
      entity: 'mailbox',
      manage: true,
    },
    {
      label: 'Nhật ký hệ thống',
      path: appRoutes.system.auditLogs,
      icon: History,
      entity: 'setting',
      manage: true,
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
    {
      path: appRoutes.system.backups,
      lazy: async () => ({
        Component: (await import('./pages/backup-list-page')).BackupListPage,
      }),
    },
    {
      path: appRoutes.system.mailboxes,
      lazy: async () => ({
        Component: (await import('./pages/mailbox-list-page')).MailboxListPage,
      }),
    },
    {
      path: appRoutes.system.auditLogs,
      lazy: async () => ({
        Component: (await import('./pages/audit-log-list-page')).AuditLogListPage,
      }),
    },
  ],
}
