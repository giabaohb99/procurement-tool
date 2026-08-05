import { useCallback, useEffect, useState } from 'react'
import { Link, Outlet, useLocation } from 'react-router-dom'
import { LogIn, LogOut, MessageCircleQuestion, Settings } from 'lucide-react'

import { api } from '@/api/client'
import { useAuth } from '@/auth/auth-context'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import HelpMainNav from '@/components/help-main-nav'
import HelpSearchBox from '@/components/help-search-box'
import { Button } from '@/components/ui/button'
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

  const displayName = user?.full_name || 'Người dùng'
  const initials = displayName.trim().split(' ').slice(-1)[0]?.[0]?.toUpperCase() || 'U'

  return (
    // Slug của mọi bài viết sinh từ cây tài liệu -> đặt provider bao ngoài để chỗ nào render
    // <Link> tới bài viết cũng lấy được đường dẫn dạng slug.
    <SlugIndexProvider tree={tree}>
    <div className="flex min-h-screen flex-col bg-background">
      <header className="sticky top-0 z-40 flex h-[4.25rem] items-center gap-6 border-b bg-background px-6 md:px-8">
        {/* Logo + gạch dọc + tên trang, giống header Trung tâm trợ giúp của hệ Văn thư */}
        <Link to="/" title="Trung tâm trợ giúp" className="flex shrink-0 items-center gap-4">
          <img src="/logo.svg" alt="DEGO Holding" className="h-8 w-auto" />
          <span aria-hidden className="h-[1.125rem] w-px bg-border" />
          <span className="text-lg font-semibold text-navy">Trung tâm trợ giúp</span>
        </Link>

        {/* Nav chính: mỗi mục gốc của cây tài liệu là một menu xổ xuống */}
        <HelpMainNav tree={tree} />

        {/* Ô tìm kiếm co giãn theo chỗ trống còn lại (tối đa 16rem) nên không đẩy tràn header */}
        {showSearch && (
          <div className="ml-auto hidden min-w-32 max-w-64 flex-1 animate-in fade-in slide-in-from-top-1 duration-200 md:block">
            <HelpSearchBox placeholder="Tìm kiếm tài liệu, hướng dẫn..." />
          </div>
        )}

        <div className="ml-auto flex shrink-0 items-center gap-3">
          <Button variant="ghost" size="sm" asChild>
            <Link to="/cau-hoi-thuong-gap">
              <MessageCircleQuestion /> <span className="hidden sm:inline">Câu hỏi thường gặp</span>
            </Link>
          </Button>

          {canManage && (
            <Button variant="outline" size="sm" asChild>
              <Link to="/admin" title="Khu quản trị tài liệu">
                <Settings /> Truy cập quản trị
              </Link>
            </Button>
          )}

          {/* Khách (chưa đăng nhập) vẫn đọc được tài liệu — chỉ mời đăng nhập khi cần quản trị */}
          {!user ? (
            <Button variant="ghost" size="sm" asChild>
              <Link to="/login" title="Đăng nhập để quản trị tài liệu">
                <LogIn /> <span className="hidden sm:inline">Đăng nhập</span>
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
        <Outlet context={{ tree } satisfies PortalOutletContext} />
      </div>

      <footer className="border-t bg-background px-6 py-6 text-center text-xs text-muted-foreground">
        © {new Date().getFullYear()} DEGO Holding · Trung tâm Hướng dẫn Sử dụng
      </footer>
    </div>
    </SlugIndexProvider>
  )
}
