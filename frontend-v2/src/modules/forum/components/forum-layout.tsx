import { LayoutGrid, MessagesSquare, Search } from 'lucide-react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'

import { DemoAccountSwitcher } from '@/app/layouts/demo-account-switcher'
import { UserMenu } from '@/app/layouts/user-menu'
import { usePermission } from '@/core/authorization/use-permission'
import { NotificationBell } from '@/shared/notifications/notification-bell'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'

import { ForumHeaderSearch } from './forum-header-search'

/**
 * Khung riêng của Diễn đàn (QĐ-D6): một cột giữa kiểu bảng tin, KHÔNG có
 * sidebar nghiệp vụ — vào đây là rời không khí chứng từ. Thanh trên giữ lại
 * đường về màn chọn phân hệ, chuông ERP và menu tài khoản; dải tab chừa sẵn
 * chỗ cho «Hướng dẫn» (QĐ-D4, vào ở F7).
 */
export function ForumLayout() {
  //  bao-CR-272: màn 1920px mà bó 672px thì hai bên trống hoác (người dùng kêu
  //  đúng câu đó) — «Diễn đàn»/«Quản trị» nới hẳn 1280px, trang ĐỌC BÀI 896px
  //  cho bài hướng dẫn dài dễ đọc, các feed còn lại 768px.
  const { pathname } = useLocation()
  const { can } = usePermission()
  //  Tab «Quản trị» (CR-263) chỉ cho người có grant diễn đàn — `can()` là tiện
  //  ẩn/hiện thôi, chốt chặn thật là `require()` trên từng API.
  const isForumAdmin = can('forum_post', 'write') || can('forum_board', 'write')
  const wide =
    pathname === appRoutes.forum.boards || pathname === appRoutes.forum.admin
  // Trang đọc một bài (`/forum/posts/:id`) — đích của bài hướng dẫn dài.
  const reading = pathname.startsWith(`${appRoutes.forum.root}/posts/`)

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

          {/*  4 tab không còn lọt màn 375px — cho dải tab cuộn ngang (giấu thanh
              cuộn) thay vì cắt cụt «Trang của tôi» và đẩy chuông/avatar ra ngoài. */}
          <nav className="ml-1 flex h-full min-w-0 items-stretch gap-1 overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden sm:ml-3">
            {/* «Diễn đàn» đứng đầu + là màn mặc định (sếp chốt 03/09/2026);
                sáng cả ở /forum/boards/:id nên KHÔNG end. */}
            <ForumTab to={appRoutes.forum.boards} label="Diễn đàn" end={false} />
            <ForumTab to={appRoutes.forum.feed} label="Bảng tin" />
            <ForumTab to={appRoutes.forum.announcements} label="Thông báo" />
            <ForumTab to={appRoutes.forum.me} label="Trang của tôi" />
            {isForumAdmin ? (
              <ForumTab to={appRoutes.forum.admin} label="Quản trị" />
            ) : null}
          </nav>

          <div className="ml-auto flex min-w-0 shrink items-center gap-1">
            {/*  Ô tìm NHÌN THẤY ĐƯỢC (bao-CR-272) — bản trước chỉ có icon kính
                lúp, người dùng tưởng diễn đàn không có tìm kiếm. Gõ là sổ top 5
                gợi ý (bao-CR-273.1). Màn hẹp mới rút về icon. */}
            <ForumHeaderSearch className="hidden md:block" />
            <Button
              asChild
              variant="ghost"
              size="icon"
              className="shrink-0 text-muted-foreground hover:text-foreground md:hidden"
            >
              <NavLink to={appRoutes.forum.search} title="Tìm bài viết">
                <Search className="size-5" />
                <span className="sr-only">Tìm bài viết</span>
              </NavLink>
            </Button>
            <NotificationBell />
            {/*  Chỉ hiện ở bản DEV — tự trả về null khi build thật. */}
            <DemoAccountSwitcher />
            <UserMenu />
          </div>
        </div>
      </header>

      <main
        className={cn(
          'mx-auto w-full flex-1 pb-10 sm:px-4',
          wide ? 'max-w-7xl' : reading ? 'max-w-4xl' : 'max-w-3xl',
        )}
      >
        <Outlet />
      </main>
    </div>
  )
}

/** Tab kiểu gạch chân dưới đáy thanh trên — khuôn cho «Hướng dẫn» sau này. */
function ForumTab({ to, label, end = true }: { to: string; label: string; end?: boolean }) {
  return (
    <NavLink
      to={to}
      end={end}
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
