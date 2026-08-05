import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'

import { useArticlePath } from '@/lib/help-slug'
import { findNode, findPath, type HelpNode } from '@/lib/help-tree'
import { cn } from '@/lib/utils'

// Sidebar trái ở trang chi tiết bài viết: cây tài liệu của MỤC GỐC đang đọc.
// Bài đang mở được tô sáng, nhánh chứa nó tự bung ra. Cùng vai trò với sidebar khu quản trị
// nhưng trỏ về đường dẫn khu người dùng (/:id).

export default function HelpSectionNav({
  tree,
  activeId,
}: {
  tree: HelpNode[]
  activeId: number | null
}) {
  const [expanded, setExpanded] = useState<Record<number, boolean>>({})
  const pathOf = useArticlePath()

  const path = activeId ? findPath(tree, activeId) : null
  // Luôn bám theo MỤC GỐC của trang đang mở (crumb đầu tiên) và liệt kê TRỌN các bài bên trong nó
  // — kể cả khi đang đứng ở chính trang danh mục của mục gốc đó. Nhờ vậy người đọc đi lại trong
  // cùng một cụm mà sidebar không đổi.
  // Mục gốc là BÀI ĐƠN (không có bài con) thì chỉ hiện đúng bài đó — KHÔNG đôn toàn bộ mục gốc
  // khác vào cho đầy, vì như vậy sidebar sẽ thay đổi hoàn toàn khi bấm sang cụm khác.
  const root = path?.length ? findNode(tree, path[0].id) : null
  const children = root?.children ?? []
  const items = children.length > 0 ? children : root ? [root] : tree

  // Tự bung nhánh chứa bài đang đọc (người dùng vẫn tự đóng/mở lại được sau đó).
  useEffect(() => {
    if (!path) return
    setExpanded((prev) => ({
      ...prev,
      ...Object.fromEntries(path.map((crumb) => [crumb.id, true])),
    }))
    // path là mảng mới mỗi lần render -> chỉ theo dõi id bài đang đọc
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeId])

  if (items.length === 0) return null

  return (
    <nav aria-label="Danh mục tài liệu" className="text-sm">
      <Link
        to={children.length > 0 ? pathOf(root!.id) : '/'}
        className="mb-3 block px-3 text-[0.6875rem] font-semibold uppercase tracking-wide text-muted-foreground transition-colors hover:text-primary"
      >
        {children.length > 0 ? root!.title : 'Danh mục tài liệu'}
      </Link>

      <ul className="space-y-0.5">
        {items.map((item) => (
          <NavNode
            key={item.id}
            node={item}
            activeId={activeId}
            expanded={expanded}
            onToggle={(id) => setExpanded((prev) => ({ ...prev, [id]: !prev[id] }))}
            pathOf={pathOf}
          />
        ))}
      </ul>
    </nav>
  )
}

function NavNode({
  node,
  activeId,
  expanded,
  onToggle,
  pathOf,
  depth = 0,
}: {
  node: HelpNode
  activeId: number | null
  expanded: Record<number, boolean>
  onToggle: (id: number) => void
  pathOf: (id: number) => string
  depth?: number
}) {
  const children = node.children || []
  const isOpen = !!expanded[node.id]
  const isActive = node.id === activeId

  return (
    <li>
      <div className="flex items-start">
        {children.length > 0 ? (
          <button
            type="button"
            aria-label={isOpen ? 'Thu gọn' : 'Mở rộng'}
            aria-expanded={isOpen}
            onClick={() => onToggle(node.id)}
            className="mt-1.5 shrink-0 rounded p-0.5 text-muted-foreground transition-colors hover:bg-secondary hover:text-navy"
          >
            <ChevronRight className={cn('size-3.5 transition-transform', isOpen && 'rotate-90')} />
          </button>
        ) : (
          // Giữ chỗ đúng bằng nút mũi tên để tiêu đề các dòng thẳng hàng nhau
          <span aria-hidden className="mt-1.5 size-4.5 shrink-0" />
        )}

        <Link
          to={pathOf(node.id)}
          style={{ paddingLeft: depth * 12 + 6 }}
          className={cn(
            'min-w-0 flex-1 rounded-md py-1.5 pr-2 leading-snug transition-colors',
            isActive
              ? 'bg-accent font-semibold text-primary'
              : 'text-navy hover:bg-secondary hover:text-primary',
          )}
        >
          {node.title}
        </Link>
      </div>

      {children.length > 0 && isOpen && (
        <ul className="mt-0.5 space-y-0.5">
          {children.map((child) => (
            <NavNode
              key={child.id}
              node={child}
              activeId={activeId}
              expanded={expanded}
              onToggle={onToggle}
              pathOf={pathOf}
              depth={depth + 1}
            />
          ))}
        </ul>
      )}
    </li>
  )
}
