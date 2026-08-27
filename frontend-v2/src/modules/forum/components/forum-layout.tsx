import { LayoutGrid, MessagesSquare } from 'lucide-react'
import { NavLink, Outlet } from 'react-router-dom'

import { DemoAccountSwitcher } from '@/app/layouts/demo-account-switcher'
import { UserMenu } from '@/app/layouts/user-menu'
import { NotificationBell } from '@/shared/notifications/notification-bell'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'

/**
 * Khung riêng của Diễn đàn (QĐ-D6): một cột giữa kiểu bảng tin, KHÔNG có
 * sidebar nghiệp vụ — vào đây là rời không khí chứng từ. Thanh trên giữ lại
 * đường về màn chọn phân hệ, chuông ERP và menu tài khoản; dải tab chừa sẵn
 * chỗ cho «Hướng dẫn» (QĐ-D4, vào ở F7).
 */
export function ForumLayout() {
  return (
    <div className="flex min-h-svh flex-col bg-muted/40">
      <header className="sticky top-0 z-10 border-b border-border bg-background">
        <div className="mx-auto flex h-14 w-full max-w-2xl items-center gap-1 px-2 sm:px-4">
          <Button
            asChild
            variant="ghost"
            size="icon"
            className="text-muted-foreground hover:text-foreground"
          >
            <NavLink to={appRoutes.launcher} title="Về màn chọn phân hệ">
              <LayoutGrid className="size-5" />
              <span className="sr-only">Về màn chọn phân hệ</span>
            </NavLink>
          </Button>

          <span className="ml-1 flex items-center gap-2 font-semibold text-navy">
            <MessagesSquare className="size-5 text-blue-600" />
            <span className="hidden sm:inline">Diễn đàn</span>
          </span>

          <nav className="ml-3 flex h-full items-stretch gap-1">
            <ForumTab to={appRoutes.forum.root} label="Bảng tin" />
            <ForumTab to={appRoutes.forum.me} label="Trang của tôi" />
          </nav>

          <div className="ml-auto flex items-center gap-1">
            <NotificationBell />
            {/*  Chỉ hiện ở bản DEV — tự trả về null khi build thật. */}
            <DemoAccountSwitcher />
            <UserMenu />
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-2xl flex-1 pb-10 sm:px-4">
        <Outlet />
      </main>
    </div>
  )
}

/** Tab kiểu gạch chân dưới đáy thanh trên — khuôn cho «Hướng dẫn» sau này. */
function ForumTab({ to, label }: { to: string; label: string }) {
  return (
    <NavLink
      to={to}
      end
      className={({ isActive }) =>
        cn(
          'flex items-center border-b-2 px-3 text-sm font-medium transition-colors',
          isActive
            ? 'border-blue-600 text-blue-600'
            : 'border-transparent text-muted-foreground hover:text-foreground',
        )
      }
    >
      {label}
    </NavLink>
  )
}
