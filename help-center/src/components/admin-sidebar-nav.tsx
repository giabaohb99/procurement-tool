import { Link } from 'react-router-dom'
import { CornerLeftUp, Eye, FileText, Folder, LayoutList } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { levelLabel } from '@/lib/help-article-actions'
import { findNode, findParent, findPath, type HelpNode } from '@/lib/help-tree'
import { cn } from '@/lib/utils'

// Sidebar khu quản trị: (1) các trang quản lý, (2) điều hướng giữa các bài viết
// liên quan tới bài đang mở — cha, anh em cùng cấp, bài con.
// Cây đầy đủ đã có ở bảng trang "Quản lý bài viết" nên không lặp lại ở đây.

export default function AdminSidebarNav({
  tree, activeId, pathname,
}: {
  tree: HelpNode[]
  activeId: number | null
  pathname: string
}) {
  const node = activeId ? findNode(tree, activeId) : null
  const parent = activeId ? findParent(tree, activeId) : null
  const depth = activeId ? (findPath(tree, activeId)?.length ?? 1) - 1 : 0

  // Anh em cùng cấp: con của cha, hoặc các mục gốc nếu bài đang mở là mục gốc
  const siblings = parent ? parent.children || [] : tree
  const children = node?.children || []

  return (
    <div className="flex flex-col gap-5 p-3">
      <NavGroup title="Trang quản lý">
        <NavLink to="/admin" active={pathname === '/admin'} icon={LayoutList}>
          Quản lý bài viết
        </NavLink>
        <NavLink to="/" icon={Eye}>Xem trang người dùng</NavLink>
      </NavGroup>

      {node && (
        <NavGroup title="Bài viết liên quan">
          {parent && (
            <Link
              to={`/admin/${parent.id}`}
              className="flex items-start gap-2 rounded-md px-2 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-secondary hover:text-navy"
            >
              <CornerLeftUp className="mt-0.5 size-4 shrink-0" />
              <span className="min-w-0">
                <span className="block truncate">{parent.title}</span>
                <span className="text-xs">Bài viết cha</span>
              </span>
            </Link>
          )}

          <SiblingList
            label={parent ? `Cùng trong "${parent.title}"` : 'Các mục gốc'}
            items={siblings}
            activeId={activeId}
          />

          {children.length > 0 && (
            <SiblingList
              label={`${levelLabel(depth + 1)} bên trong (${children.length})`}
              items={children}
              activeId={null}
            />
          )}
        </NavGroup>
      )}
    </div>
  )
}

function NavGroup({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="mb-1.5 px-2 text-[0.6875rem] font-semibold uppercase tracking-wide text-muted-foreground">
        {title}
      </div>
      <div className="space-y-0.5">{children}</div>
    </div>
  )
}

function NavLink({
  to, icon: Icon, active = false, children,
}: {
  to: string
  icon: typeof LayoutList
  active?: boolean
  children: React.ReactNode
}) {
  return (
    <Link
      to={to}
      className={cn(
        'flex items-center gap-2 rounded-md px-2 py-1.5 text-sm font-medium transition-colors',
        active ? 'bg-accent text-accent-foreground' : 'text-navy hover:bg-secondary',
      )}
    >
      <Icon className="size-4 shrink-0" />
      {children}
    </Link>
  )
}

/** Danh sách bài viết cùng nhóm — bài đang mở được tô sáng. */
function SiblingList({
  label, items, activeId,
}: {
  label: string
  items: HelpNode[]
  activeId: number | null
}) {
  if (items.length === 0) return null

  return (
    <div className="mt-3">
      <div className="mb-1 truncate px-2 text-xs text-muted-foreground">{label}</div>
      <ul className="space-y-0.5">
        {items.map((item) => {
          const isActive = item.id === activeId
          const hasChildren = !!item.children?.length
          return (
            <li key={item.id}>
              <Link
                to={`/admin/${item.id}`}
                className={cn(
                  'flex items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors',
                  isActive
                    ? 'bg-accent font-semibold text-accent-foreground'
                    : 'text-navy hover:bg-secondary',
                )}
              >
                {hasChildren
                  ? <Folder className="size-4 shrink-0 text-primary" strokeWidth={1.75} />
                  : <FileText className="size-4 shrink-0 text-muted-foreground" strokeWidth={1.75} />}
                <span className="min-w-0 flex-1 truncate">{item.title}</span>
                {hasChildren && (
                  <Badge variant="outline" className="shrink-0 px-1.5 font-normal text-muted-foreground">
                    {item.children!.length}
                  </Badge>
                )}
              </Link>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
