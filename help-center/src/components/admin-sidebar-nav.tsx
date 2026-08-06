import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  CornerLeftUp, Eye, History, LayoutList, LayoutTemplate, MessageCircleQuestion,
} from 'lucide-react'

import AdminSidebarTreeItem from '@/components/admin-sidebar-tree-item'
import { findNode, findParent, findPath, type HelpNode } from '@/lib/help-tree'
import { useHelpTreeDnd } from '@/lib/use-help-tree-dnd'
import { cn } from '@/lib/utils'

// Sidebar khu quản trị: (1) các trang quản lý, (2) điều hướng tới bài cha và các bài
// cùng cấp với bài đang mở — mỗi bài có bài con thì SỔ XUỐNG xem được ngay tại đây.
// Cây đầy đủ vẫn nằm ở bảng "Quản lý bài viết" (nơi kéo-thả, xóa, thêm).

export default function AdminSidebarNav({
  tree, activeId, pathname, onTreeChanged,
}: {
  tree: HelpNode[]
  activeId: number | null
  pathname: string
  /** Nạp lại cây sau khi kéo-thả đổi mục cha / thứ tự. */
  onTreeChanged: () => Promise<void> | void
}) {
  const node = activeId ? findNode(tree, activeId) : null
  const parent = activeId ? findParent(tree, activeId) : null

  // Anh em cùng cấp: con của cha, hoặc các mục gốc nếu bài đang mở là mục gốc
  const siblings = parent ? parent.children || [] : tree

  // Nhánh chứa bài đang mở luôn bung sẵn. Tính TRỰC TIẾP khi render chứ không nhét vào state
  // qua useEffect: cây tài liệu tải xong sau lần render đầu, effect chạy trên cây rỗng sẽ
  // ra tập rỗng và không bao giờ tính lại.
  const path = activeId ? findPath(tree, activeId) : null
  const autoOpen = new Set(path ? path.map((crumb) => crumb.id) : [])

  // Người dùng tự đóng/mở thì ghi đè lên mặc định; đổi bài là xóa hết ghi đè
  const [overrides, setOverrides] = useState<Map<number, boolean>>(new Map())
  useEffect(() => { setOverrides(new Map()) }, [activeId])

  const isOpen = (id: number) => overrides.get(id) ?? autoOpen.has(id)
  const toggle = (id: number) => setOverrides((prev) => new Map(prev).set(id, !isOpen(id)))

  // Kéo-thả đổi mục cha / thứ tự, dùng chung logic với bảng cây /admin.
  // Thứ tự mới được tính trên cây ĐẦY ĐỦ nên dù sidebar chỉ hiện một phần cây vẫn ghi đúng.
  const dnd = useHelpTreeDnd({
    tree,
    onChanged: onTreeChanged,
    onDroppedInside: (parentId) => setOverrides((prev) => new Map(prev).set(parentId, true)),
  })

  return (
    <div className="flex flex-col gap-5 p-3">
      <NavGroup title="Trang quản lý">
        <NavLink to="/admin" active={pathname === '/admin'} icon={LayoutList}>
          Quản lý bài viết
        </NavLink>
        <NavLink to="/admin/trang-chu" active={pathname === '/admin/trang-chu'} icon={LayoutTemplate}>
          Bố cục trang chủ
        </NavLink>
        <NavLink to="/admin/faq" active={pathname === '/admin/faq'} icon={MessageCircleQuestion}>
          Câu hỏi thường gặp
        </NavLink>
        <NavLink to="/admin/lich-su" active={pathname === '/admin/lich-su'} icon={History}>
          Lịch sử thay đổi
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

          {siblings.length > 0 && (
            <div className="mt-3">
              <div className="mb-1 truncate px-2 text-xs text-muted-foreground">
                {parent ? `Cùng trong "${parent.title}"` : 'Các mục gốc'}
              </div>
              <ul className="space-y-0.5">
                {siblings.map((item) => (
                  <AdminSidebarTreeItem
                    key={item.id}
                    node={item}
                    activeId={activeId}
                    isOpen={isOpen}
                    onToggle={toggle}
                    dnd={dnd}
                  />
                ))}
              </ul>
            </div>
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
