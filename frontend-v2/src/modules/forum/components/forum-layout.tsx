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
      {/*  Header trải HẾT bề ngang (không bó max-w-2xl như cột feed) — bó chung
          với feed thì gặp tên tài khoản dài là tab bị ép gãy chữ xuống hai dòng. */}
      <header className="sticky top-0 z-10 border-b border-border bg-background">
        <div className="flex h-14 w-full items-center gap-1 px-2 sm:px-6">
          <Button
            asChild
            variant="ghost"
            size="icon"
            className="shrink-0 text-muted-foreground hover:text-foreground"
          >
            <NavLink to={appRoutes.launcher} title="Về màn chọn phân hệ">
              <LayoutGrid className="size-5" />
              <span className="sr-only">Về màn chọn phân hệ</span>
            </NavLink>
          </Button>

          <span className="ml-1 flex shrink-0 items-center gap-2 whitespace-nowrap font-semibold text-navy">
            <MessagesSquare className="size-5 text-blue-600" />
            <span className="hidden md:inline">Diễn đàn</span>
          </span>

          <nav className="ml-1 flex h-full shrink-0 items-stretch gap-1 sm:ml-3">
            <ForumTab to={appRoutes.forum.root} label="Bảng tin" />
            <ForumTab to={appRoutes.forum.announcements} label="Thông báo" />
            <ForumTab to={appRoutes.forum.me} label="Trang của tôi" />
          </nav>

          <div className="ml-auto flex min-w-0 shrink items-center gap-1">
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
      // Đang giữa trang mà bấm tab (kể cả tab đang mở) thì về đầu trang —
      // SPA đổi route không tự cuộn, người dùng tưởng bấm không ăn.
      onClick={() => window.scrollTo({ top: 0 })}
      className={({ isActive }) =>
        cn(
          'flex items-center whitespace-nowrap border-b-2 px-2 text-sm font-medium transition-colors sm:px-3',
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
