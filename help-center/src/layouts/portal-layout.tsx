import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, Outlet, useLocation } from 'react-router-dom'
import { LogIn, LogOut, Menu, MessageCircleQuestion, PanelLeft, Settings } from 'lucide-react'

import { api } from '@/api/client'
import { useAuth } from '@/auth/auth-context'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import HelpMainNav from '@/components/help-main-nav'
import HelpSearchBox from '@/components/help-search-box'
import { Button } from '@/components/ui/button'
import { DESKTOP_QUERY, useMediaQuery } from '@/hooks/use-media-query'
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { SlugIndexProvider } from '@/lib/help-slug'
import { buildTree, type HelpNode } from '@/lib/help-tree'

// Khu NGƯỜI DÙNG (/) — header gọn (logo + tài khoản), chỉ đọc.
// Mọi thao tác thêm/sửa/xóa nằm ở khu quản trị (/admin).

export interface PortalOutletContext {
  tree: HelpNode[]
  sidebar: PortalSidebarState
}

/** Trạng thái danh mục bên trái — header giữ, trang con (help-portal-shell) dùng lại. */
export interface PortalSidebarState {
  /** Màn rộng: cột danh mục đang hiện. Màn hẹp: ngăn kéo đang mở. */
  open: boolean
  toggle: () => void
  close: () => void
  /** Bề ngang đủ cho danh mục dạng cột hay chưa (< 1024px thì phải dùng ngăn kéo). */
  isDesktop: boolean
  /** Trang đang mở có danh mục hay không — trang chủ/FAQ thì không, nên ẩn nút ☰. */
  setAvailable: (value: boolean) => void
}

/** id của ô tìm kiếm lớn giữa trang chủ — header theo dõi nó để biết khi nào cần tự hiện ô của mình. */
export const HERO_SEARCH_ID = 'hc-hero-search'

/** Chiều cao header (4.25rem) — dùng làm rootMargin để tính "ô tìm kiếm đã chui xuống dưới header". */
const HEADER_HEIGHT_PX = 68

export default function PortalLayout() {
  const { user, can, logout } = useAuth()
  const { pathname } = useLocation()
  const canManage = can('help_article', 'write')
  const [tree, setTree] = useState<HelpNode[]>([])

  // Ô tìm kiếm nằm ở header là ô tìm kiếm DUY NHẤT của khu người dùng (các trang trong không còn
  // dải breadcrumb + tìm kiếm riêng nữa). Ngoại lệ: ở đầu trang chủ đã có ô lớn giữa hero, nên chỉ
  // hiện sau khi ô đó cuộn khuất sau header.
  const [showSearch, setShowSearch] = useState(true)
  useEffect(() => {
    const hero = document.getElementById(HERO_SEARCH_ID)
    if (!hero) { setShowSearch(true); return }
    setShowSearch(false)
    const observer = new IntersectionObserver(
      ([entry]) => setShowSearch(!entry.isIntersecting),
      { rootMargin: `-${HEADER_HEIGHT_PX}px 0px 0px 0px` },
    )
    observer.observe(hero)
    return () => observer.disconnect()
  }, [pathname])

  const loadTree = useCallback(async () => {
    try {
      const res = await api.get('/api/v1/help-center/tree')
      setTree(buildTree(res.data.data))
    } catch {
      // client.ts đã toast lỗi; giữ cây cũ để UI không trắng
    }
  }, [])

  useEffect(() => { loadTree() }, [loadTree])

  // ---- Danh mục bên trái ----
  // Màn rộng: mở sẵn thành một cột. Màn hẹp (< 1024): là ngăn kéo phủ lên nên phải đóng sẵn,
  // và đóng lại mỗi lần chuyển trang — nếu không, bấm một bài trong ngăn kéo xong nó vẫn che nội dung.
  const isDesktop = useMediaQuery(DESKTOP_QUERY)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [sidebarAvailable, setSidebarAvailable] = useState(false)

  useEffect(() => { setSidebarOpen(isDesktop) }, [isDesktop])
  useEffect(() => { if (!isDesktop) setSidebarOpen(false) }, [pathname, isDesktop])

  const sidebar = useMemo(() => ({
    open: sidebarOpen,
    toggle: () => setSidebarOpen((v) => !v),
    close: () => setSidebarOpen(false),
    isDesktop,
    setAvailable: setSidebarAvailable,
  }), [sidebarOpen, isDesktop])

  const displayName = user?.full_name || 'Người dùng'
  const initials = displayName.trim().split(' ').slice(-1)[0]?.[0]?.toUpperCase() || 'U'

  return (
    // Slug của mọi bài viết sinh từ cây tài liệu -> đặt provider bao ngoài để chỗ nào render
    // <Link> tới bài viết cũng lấy được đường dẫn dạng slug.
    <SlugIndexProvider tree={tree}>
    <div className="flex min-h-screen flex-col bg-background">
      <header className="sticky top-0 z-[60] flex h-[4.25rem] items-center gap-4 border-b bg-background px-6 md:px-8 lg:gap-6">
        {/* Bật/tắt danh mục — chỉ hiện ở trang CÓ danh mục (không phải trang chủ / câu hỏi thường gặp).
            Màn hẹp là nút ☰ mở ngăn kéo; màn rộng là nút thu/mở cột, thu lại thì mục lục hiện ra. */}
        {sidebarAvailable && (
          <Button
            variant="ghost" size="icon" className="-ml-2 shrink-0"
            aria-expanded={sidebarOpen}
            title={sidebarOpen ? 'Ẩn danh mục tài liệu' : 'Hiện danh mục tài liệu'}
            onClick={sidebar.toggle}
          >
            {isDesktop ? <PanelLeft /> : <Menu />}
          </Button>
        )}

        {/* Logo + gạch dọc + tên trang, giống header Trung tâm trợ giúp của hệ Văn thư */}
        <Link to="/" title="Trung tâm trợ giúp" className="flex shrink-0 items-center gap-4">
          <img src="/logo.svg" alt="DEGO Holding" className="h-8 w-auto" />
          {/* Dưới lg bỏ chữ, chỉ giữ logo — có thêm nút ☰ rồi thì header không đủ chỗ */}
          <span aria-hidden className="hidden h-[1.125rem] w-px bg-border lg:block" />
          <span className="hidden text-lg font-semibold text-navy lg:inline">Trung tâm trợ giúp</span>
        </Link>

        {/* Nav chính: mỗi mục gốc của cây tài liệu là một menu xổ xuống */}
        <HelpMainNav tree={tree} />

        {/* Ô tìm kiếm co giãn theo chỗ trống còn lại (tối đa 16rem) nên không đẩy tràn header */}
        {showSearch && (
          <div className="ml-auto hidden min-w-32 max-w-64 flex-1 animate-in fade-in slide-in-from-top-1 duration-200 md:block">
            <HelpSearchBox placeholder="Tìm kiếm tài liệu, hướng dẫn..." />
          </div>
        )}

        {/* Dưới lg các nút chỉ còn icon (nhãn vẫn nằm ở title để rê chuột đọc được) — bày đủ chữ
            thì header tràn ngang ngay ở khổ máy tính bảng */}
        <div className="ml-auto flex shrink-0 items-center gap-1 lg:gap-3">
          <Button variant="ghost" size="sm" asChild>
            <Link to="/cau-hoi-thuong-gap" title="Câu hỏi thường gặp">
              <MessageCircleQuestion /> <span className="hidden lg:inline">Câu hỏi thường gặp</span>
            </Link>
          </Button>

          {canManage && (
            <Button variant="outline" size="sm" asChild>
              <Link to="/admin" title="Khu quản trị tài liệu">
                <Settings /> <span className="hidden lg:inline">Truy cập quản trị</span>
              </Link>
            </Button>
          )}

          {/* Khách (chưa đăng nhập) vẫn đọc được tài liệu — chỉ mời đăng nhập khi cần quản trị */}
          {!user ? (
            <Button variant="ghost" size="sm" asChild>
              <Link to="/login" title="Đăng nhập để quản trị tài liệu">
                <LogIn /> <span className="hidden lg:inline">Đăng nhập</span>
              </Link>
            </Button>
          ) : (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="rounded-full" title="Tài khoản">
                <Avatar className="size-8">
                  {user?.avatar && <AvatarImage src={user.avatar} alt={displayName} />}
                  <AvatarFallback className="bg-primary text-sm font-semibold text-primary-foreground">
                    {initials}
                  </AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel>
                <div className="font-semibold text-navy">{displayName}</div>
                <div className="text-xs font-normal text-muted-foreground">
                  {user?.emp_code || user?.email}
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem variant="destructive" onClick={logout}>
                <LogOut /> Đăng xuất
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
          )}
        </div>
      </header>

      <div className="flex-1">
        <Outlet context={{ tree, sidebar } satisfies PortalOutletContext} />
      </div>

      <footer className="border-t bg-background px-6 py-6 text-center text-xs text-muted-foreground">
        © {new Date().getFullYear()} DEGO Holding · Trung tâm Hướng dẫn Sử dụng
      </footer>
    </div>
    </SlugIndexProvider>
  )
}
