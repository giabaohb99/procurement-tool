import { useCallback, useEffect, useState } from 'react'
import { Link, Navigate, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { ChevronRight, Eye, FilePlus2, FolderPlus, LayoutList, LogOut, PanelLeft } from 'lucide-react'

import { api } from '@/api/client'
import { useAuth } from '@/auth/auth-context'
import HelpSearchBox from '@/components/help-search-box'
import HelpTreeNav from '@/components/help-tree-nav'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/lib/utils'
import { createArticle } from '@/lib/help-article-actions'
import { buildTree, findNode, findPath, type HelpNode } from '@/lib/help-tree'

// Khu QUẢN TRỊ (/admin) — sidebar cây tài liệu + trình soạn thảo.
// Chỉ user có quyền help_article/write vào được; user thường bị đẩy về khu người dùng.

export interface AdminOutletContext {
  loadTree: () => Promise<void>
  tree: HelpNode[]
}

export default function AdminLayout() {
  const { user, can, logout } = useAuth()
  const loc = useLocation()
  const nav = useNavigate()
  const canWrite = can('help_article', 'write')
  const canCreate = can('help_article', 'create')

  const [tree, setTree] = useState<HelpNode[]>([])
  const [expanded, setExpanded] = useState<Set<number>>(new Set())
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const match = loc.pathname.match(/^\/admin\/(\d+)/)
  const activeId = match ? parseInt(match[1], 10) : null

  const loadTree = useCallback(async () => {
    try {
      const res = await api.get('/api/v1/help-center/tree')
      setTree(buildTree(res.data.data))
    } catch {
      // client.ts đã toast lỗi; giữ cây cũ để UI không trắng
    }
  }, [])

  useEffect(() => { loadTree() }, [loadTree])

  // Mở sẵn các thư mục cha của bài đang sửa
  useEffect(() => {
    if (!activeId || tree.length === 0) return
    const path = findPath(tree, activeId)
    if (!path) return
    setExpanded((prev) => {
      const next = new Set(prev)
      path.slice(0, -1).forEach((c) => next.add(c.id))
      return next
    })
  }, [activeId, tree])

  if (!canWrite) return <Navigate to="/" replace />

  const toggleExpand = (id: number) =>
    setExpanded((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })

  /** Tạo bài mới rồi mở luôn. parentId = null -> mục gốc. */
  const addArticle = async (parentId: number | null) => {
    const parent = parentId ? findNode(tree, parentId) : null
    const depth = parentId ? (findPath(tree, parentId)?.length ?? 1) : 0
    const id = await createArticle(parentId, parent?.children?.length ?? tree.length, depth)
    if (!id) return
    if (parentId) setExpanded((prev) => new Set(prev).add(parentId))
    await loadTree()
    nav(`/admin/${id}`)
  }

  const breadcrumbs = activeId ? findPath(tree, activeId) : null
  const displayName = user?.full_name || 'Người dùng'
  const initials = displayName.trim().split(' ').slice(-1)[0]?.[0]?.toUpperCase() || 'U'

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {sidebarOpen && (
        <aside className="flex w-80 shrink-0 flex-col border-r">
          <div className="flex h-14 items-center justify-between gap-2 border-b px-4">
            <Link to="/admin" title="Trang quản trị" className="flex items-center gap-2">
              <img src="/logo.svg" alt="DEGO Holding" className="h-7 w-auto" />
              <Badge variant="secondary" className="bg-amber-100 text-amber-700">Quản trị</Badge>
            </Link>
            {canCreate && (
              <div className="flex gap-1">
                {activeId && (findPath(tree, activeId)?.length ?? 3) < 3 && (
                  <Button variant="ghost" size="icon" title="Thêm bài viết con"
                          onClick={() => addArticle(activeId)}>
                    <FilePlus2 />
                  </Button>
                )}
                <Button variant="ghost" size="icon" title="Thêm mục gốc"
                        onClick={() => addArticle(null)}>
                  <FolderPlus />
                </Button>
              </div>
            )}
          </div>

          <div className="border-b p-2">
            <Link
              to="/admin"
              className={cn(
                'flex items-center gap-2 rounded-md px-2 py-1.5 text-sm font-medium transition-colors',
                loc.pathname === '/admin'
                  ? 'bg-accent text-accent-foreground'
                  : 'text-navy hover:bg-secondary',
              )}
            >
              <LayoutList className="size-4" /> Quản lý bài viết
            </Link>
          </div>

          <div className="flex-1 overflow-y-auto p-2">
            <HelpTreeNav tree={tree} activeId={activeId} expanded={expanded}
                         onToggle={toggleExpand} basePath="/admin" />
          </div>
        </aside>
      )}

      <main className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <header className="sticky top-0 z-10 flex h-14 shrink-0 items-center gap-3 border-b bg-background px-4">
          <Button variant="ghost" size="icon" title="Ẩn/hiện danh mục"
                  onClick={() => setSidebarOpen((v) => !v)}>
            <PanelLeft />
          </Button>
          <Separator orientation="vertical" className="!h-4" />

          <nav aria-label="breadcrumb" className="min-w-0 flex-1">
            <ol className="flex items-center gap-1.5 overflow-hidden text-sm text-muted-foreground">
              <li className="shrink-0">
                <Link to="/admin" className="hover:text-primary">Quản trị tài liệu</Link>
              </li>
              {breadcrumbs?.map((b, i) => (
                <li key={b.id} className="flex min-w-0 items-center gap-1.5">
                  <ChevronRight className="size-3.5 shrink-0" />
                  {i === breadcrumbs.length - 1 ? (
                    <span className="truncate text-navy">{b.title}</span>
                  ) : (
                    <Link to={`/admin/${b.id}`} className="truncate hover:text-primary">{b.title}</Link>
                  )}
                </li>
              ))}
            </ol>
          </nav>

          <div className="flex shrink-0 items-center gap-3">
            <HelpSearchBox basePath="/admin" className="hidden w-56 xl:block" />

            <Button variant="outline" size="sm" asChild>
              <Link to={activeId ? `/${activeId}` : '/'} title="Xem giao diện người dùng">
                <Eye /> <span className="hidden sm:inline">Xem trang người dùng</span>
              </Link>
            </Button>

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

        <div className="flex-1 overflow-y-auto">
          <Outlet context={{ loadTree, tree } satisfies AdminOutletContext} />
        </div>
      </main>
    </div>
  )
}
