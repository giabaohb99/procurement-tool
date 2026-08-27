import { Link, Outlet } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { env } from '@/core/config/env'
import { AssistantWidget } from '@/modules/assistant/components/assistant-widget'
import { appRoutes } from '@/shared/constants/app-routes'
import { NotificationBell } from '@/shared/notifications/notification-bell'
import { DemoAccountSwitcher } from './demo-account-switcher'
import { UserMenu } from './user-menu'

/**
 * Khung của màn CHỌN PHÂN HỆ: chỉ thanh trên, không menu trái.
 * Vào hẳn một phân hệ rồi thì đổi sang `ModuleLayout` (có sidebar).
 */
export function LauncherLayout() {
  const { can } = usePermission()
  return (
    <div className="flex min-h-screen flex-col bg-canvas">
      <header className="flex h-14 shrink-0 items-center justify-between border-b border-border bg-background px-4">
        <Link
          to={appRoutes.launcher}
          className="flex items-center transition-opacity hover:opacity-80"
          title="Về màn chọn phân hệ / Trang chủ"
        >
          <img src="/logo.svg" alt={env.appName} className="h-7 w-auto" />
        </Link>
        {/* Chuông có mặt ở CẢ HAI khung: việc cần xử lý không đợi người dùng
            vào hẳn một phân hệ mới được báo. */}
        <div className="flex items-center gap-1">
          <NotificationBell />
          {/*  Có mặt ở cả hai khung: người trình diễn hay đổi vai ngay từ màn
               chọn phân hệ, vì mỗi vai thấy một bộ phân hệ khác nhau. */}
          <DemoAccountSwitcher />
          <UserMenu />
        </div>
      </header>

      {/* flex-col để trang con canh giữa theo chiều dọc bằng `flex-1 justify-center`. */}
      <main className="flex flex-1 flex-col">
        <Outlet />
      </main>

      {/* Bong bóng Trợ lý AI cũng có mặt ở màn chọn phân hệ — chỉ ai có quyền mới thấy. */}
      {can('assistant', 'read') && <AssistantWidget />}
    </div>
  )
}
