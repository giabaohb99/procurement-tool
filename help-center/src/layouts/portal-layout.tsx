import { useCallback, useEffect, useState } from 'react'
import { Link, Outlet } from 'react-router-dom'
import { LogOut, Settings } from 'lucide-react'

import { api } from '@/api/client'
import { useAuth } from '@/auth/auth-context'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { buildTree, type HelpNode } from '@/lib/help-tree'

// Khu NGƯỜI DÙNG (/) — header gọn (logo + tài khoản), chỉ đọc.
// Mọi thao tác thêm/sửa/xóa nằm ở khu quản trị (/admin).

export interface PortalOutletContext {
  tree: HelpNode[]
}

export default function PortalLayout() {
  const { user, can, logout } = useAuth()
  const canManage = can('help_article', 'write')
  const [tree, setTree] = useState<HelpNode[]>([])

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
    <div className="flex min-h-screen flex-col bg-background">
      <header className="sticky top-0 z-40 flex h-[4.25rem] items-center gap-6 border-b bg-background px-6 md:px-8">
        <Link to="/" title="Trung tâm Hướng dẫn Sử dụng" className="shrink-0">
          <img src="/logo.svg" alt="DEGO Holding" className="h-8 w-auto" />
        </Link>

        <div className="ml-auto flex shrink-0 items-center gap-3">
          {canManage && (
            <Button variant="outline" size="sm" asChild>
              <Link to="/admin" title="Khu quản trị tài liệu">
                <Settings /> Quản trị
              </Link>
            </Button>
          )}

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
        </div>
      </header>

      <div className="flex-1">
        <Outlet context={{ tree } satisfies PortalOutletContext} />
      </div>

      <footer className="border-t bg-background px-6 py-6 text-center text-xs text-muted-foreground">
        © {new Date().getFullYear()} DEGO Holding · Trung tâm Hướng dẫn Sử dụng
      </footer>
    </div>
  )
}
