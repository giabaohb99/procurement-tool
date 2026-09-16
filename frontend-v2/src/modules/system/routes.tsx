import {
  AtSign,
  Database,
  FileDown,
  FileUp,
  History,
  LayoutDashboard,
  MailCheck,
  MonitorSmartphone,
  ScrollText,
  Settings,
  ShieldCheck,
  SlidersHorizontal,
} from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Phân hệ QUẢN TRỊ HỆ THỐNG.
 *
 * Quản lý cấu hình hệ thống, sao lưu CSDL, nhật ký hệ thống, phân quyền tài khoản
 * và các tác vụ quản trị.
 *
 * ⚠️ **Phân quyền tài khoản nằm ở ĐÂY từ 14/09/2026** (duoc-CR-396). Trước đó nó
 * ở phân hệ Nhân sự, và docstring này từng ghi đúng câu ngược lại — sửa chỗ này
 * thì nhớ soát luôn `hr/routes.tsx`.
 */
export const systemModule: ErpModule = {
  id: 'system',
  // Nhãn ngắn để không xuống dòng trong ô 112px; mô tả bên dưới nói rõ phạm vi.
  title: 'Quản trị',
  description: 'Cấu hình hệ thống, sao lưu CSDL và các tác vụ quản trị.',
  icon: Settings,
  path: appRoutes.system.root,
  accent: 'bg-slate-500/10 text-slate-600 dark:text-slate-400',
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
      //  duoc-CR-397: tách khỏi Cấu hình hệ thống. Là NỘI DUNG soạn thảo (tiêu
      //  đề + HTML từng bước), sửa đi sửa lại và mỗi mẫu mở tiếp một trang con —
      //  khác hẳn mấy ô thông số gõ một lần của Cấu hình.
      label: 'Mẫu email thông báo',
      path: appRoutes.system.emailTemplates,
      icon: MailCheck,
      entity: 'setting',
      manage: true,
      //  Trang con sửa nội dung nằm dưới đường dẫn này nên tự khớp, khai
      //  `matchPaths` là thừa.
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
      //  bao-CR-407: đổi tên từ «Nhật ký hệ thống». Màn này đọc `tab_audit_log`
      //  — dấu vết NGHIỆP VỤ theo từng chứng từ. Tên cũ giành mất chỗ của màn
      //  *Nhật ký hệ thống* thật (bên dưới), thứ lấy lượt gọi API làm xương sống.
      label: 'Nhật ký nghiệp vụ',
      path: appRoutes.system.auditLogs,
      icon: History,
      entity: 'setting',
      manage: true,
    },
    {
      //  bao-CR-407 (CR-312 P5). Hai khóa, KHÔNG `manage`: backend chỉ đòi
      //  `audit.read` HOẶC `setting.read` để mở màn (`_can_read_logs`), còn
      //  `change_log.read` quyết định có thấy giá trị trước/sau hay không —
      //  không có cửa ghi nào ở đây, nhật ký là thứ chỉ đọc.
      label: 'Nhật ký hệ thống',
      path: appRoutes.system.logs,
      icon: ScrollText,
      entities: ['audit', 'setting'],
    },
    {
      // bao-CR-395: khóa riêng `login_session` — Quản lý thu mua KHÔNG tự có
      // (nằm trong `_SYS_ENTITIES`), vai trò cũ trên hệ đang chạy phải được tick.
      label: 'Phiên đăng nhập',
      path: appRoutes.system.sessions,
      icon: MonitorSmartphone,
      entity: 'login_session',
      manage: true,
    },
    {
      //  duoc-CR-396: dời từ phân hệ Nhân sự sang đây. Khai ai được làm gì là
      //  việc QUẢN TRỊ HỆ THỐNG — màn này gác cả 55 khóa quyền của mọi phân hệ
      //  chứ không riêng hồ sơ nhân viên, nên nó đứng cạnh *Cấu hình hệ thống*
      //  và *Phiên đăng nhập* chứ không cạnh *Phòng ban* / *Chức vụ*.
      //
      //  `manage: true`: quyền `read` thuần trên `role` chỉ để đổ ô chọn vai trò
      //  ở nơi khác; vào được màn này thì phải sửa được, kẻo mở ra chỉ để nhìn
      //  một ma trận xám.
      label: 'Phân quyền tài khoản',
      path: appRoutes.system.permissions,
      icon: ShieldCheck,
      entity: 'role',
      manage: true,
    },
    {
      label: 'Nhập dữ liệu',
      path: appRoutes.system.imports,
      icon: FileUp,
      entity: 'import',
      group: 'Nhập / Xuất dữ liệu',
    },
    {
      label: 'Xuất dữ liệu',
      path: appRoutes.system.exports,
      icon: FileDown,
      entity: 'setting',
      group: 'Nhập / Xuất dữ liệu',
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
      path: appRoutes.system.emailTemplates,
      lazy: async () => ({
        Component: (await import('./pages/email-template-list-page')).EmailTemplateListPage,
      }),
    },
    {
      path: appRoutes.system.emailTemplate(':event'),
      lazy: async () => ({
        Component: (await import('./pages/email-template-editor-page')).EmailTemplateEditorPage,
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
    {
      path: appRoutes.system.logs,
      lazy: async () => ({
        Component: (await import('./pages/system-log-list-page')).SystemLogListPage,
      }),
    },
    {
      path: appRoutes.system.sessions,
      lazy: async () => ({
        Component: (await import('./pages/login-session-list-page')).LoginSessionListPage,
      }),
    },
    {
      path: appRoutes.system.imports,
      lazy: async () => ({
        Component: (await import('./pages/import-list-page')).ImportListPage,
      }),
    },
    {
      path: appRoutes.system.importDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/import-detail-page')).ImportDetailPage,
      }),
    },
    {
      path: appRoutes.system.exports,
      lazy: async () => ({
        Component: (await import('./pages/export-list-page')).ExportListPage,
      }),
    },
    {
      path: appRoutes.system.exportDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/export-detail-page')).ExportDetailPage,
      }),
    },
    //  ── Phân quyền tài khoản (duoc-CR-396, dời từ phân hệ Nhân sự) ────────
    {
      path: appRoutes.system.permissions,
      lazy: async () => ({
        Component: (await import('./pages/role-permission-page')).RolePermissionPage,
      }),
    },
    {
      path: appRoutes.system.userPermissionDetail(':userId'),
      lazy: async () => ({
        Component: (await import('./pages/user-permission-detail-page'))
          .UserPermissionDetailPage,
      }),
    },
  ],
}
