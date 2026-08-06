import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'

import { useArticlePath } from '@/lib/help-slug'
import { findPath, type HelpNode } from '@/lib/help-tree'
import { cn } from '@/lib/utils'

// Sidebar trái ở trang danh mục / bài viết: liệt kê TOÀN BỘ mục gốc (giống help center của Lark),
// chỉ bung nhánh chứa bài đang đọc. Trước đây sidebar chỉ hiện đúng cụm của mục gốc đang mở nên
// người đọc không thấy hệ thống tài liệu còn những phần nào và phải quay về trang chủ để đi tiếp.

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

  // Chỉ bung đúng nhánh chứa bài đang đọc và ĐÓNG các nhánh còn lại mỗi lần chuyển bài —
  // gộp thêm vào trạng thái cũ thì đọc vài bài là cả cây bung hết, sidebar dài không tra được.
  // Trong cùng một trang, người đọc vẫn tự đóng/mở tay thoải mái.
  useEffect(() => {
    setExpanded(path ? Object.fromEntries(path.map((crumb) => [crumb.id, true])) : {})
    // path là mảng mới mỗi lần render -> chỉ theo dõi id bài đang đọc
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeId])

  if (tree.length === 0) return null

  return (
    <nav aria-label="Danh mục tài liệu" className="text-sm">
      <Link
        to="/"
        className="mb-3 block px-3 text-[0.6875rem] font-semibold uppercase tracking-wide text-muted-foreground transition-colors hover:text-primary"
      >
        Danh mục tài liệu
      </Link>

      <ul className="space-y-0.5">
        {tree.map((item) => (
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
