import { Link } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'

import { cn } from '@/lib/utils'
import type { HelpNode } from '@/lib/help-tree'

// Cây thư mục bài viết ở sidebar khu quản trị. Node có con = thư mục (bấm mũi tên để mở/đóng),
// node lá = bài viết. basePath quyết định điều hướng sang khu người dùng ('') hay quản trị ('/admin').

interface TreeNodeProps {
  node: HelpNode
  activeId: number | null
  expanded: Set<number>
  onToggle: (id: number) => void
  basePath: string
  level?: number
}

function TreeNode({ node, activeId, expanded, onToggle, basePath, level = 0 }: TreeNodeProps) {
  const isFolder = !!node.children?.length
  const isExpanded = expanded.has(node.id)
  const isActive = activeId === node.id

  return (
    <li>
      <Link
        to={`${basePath}/${node.id}`}
        style={{ marginLeft: level * 16 }}
        onClick={() => { if (isFolder && !isExpanded) onToggle(node.id) }}
        className={cn(
          'flex items-center rounded-lg px-2 py-1.5 text-sm transition-colors',
          isActive ? 'bg-accent font-semibold text-accent-foreground' : 'text-navy hover:bg-muted',
        )}
      >
        {isFolder ? (
          <span
            role="button"
            aria-label={isExpanded ? 'Thu gọn' : 'Mở rộng'}
            onClick={(e) => { e.preventDefault(); e.stopPropagation(); onToggle(node.id) }}
            className="grid size-6 shrink-0 place-items-center rounded text-muted-foreground hover:bg-slate-200"
          >
            <ChevronRight className={cn('size-3.5 transition-transform', isExpanded && 'rotate-90')} />
          </span>
        ) : (
          <span className="w-6 shrink-0" />
        )}
        <span className="truncate">{node.title}</span>
      </Link>

      {isFolder && isExpanded && (
        <ul>
          {node.children!.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              activeId={activeId}
              expanded={expanded}
              onToggle={onToggle}
              basePath={basePath}
              level={level + 1}
            />
          ))}
        </ul>
      )}
    </li>
  )
}

export default function HelpTreeNav({
  tree, activeId, expanded, onToggle, basePath = '',
}: {
  tree: HelpNode[]
  activeId: number | null
  expanded: Set<number>
  onToggle: (id: number) => void
  basePath?: string
}) {
  if (tree.length === 0) {
    return <div className="p-4 text-center text-sm text-muted-foreground">Chưa có nội dung</div>
  }

  return (
    <ul className="space-y-0.5">
      {tree.map((node) => (
        <TreeNode
          key={node.id}
          node={node}
          activeId={activeId}
          expanded={expanded}
          onToggle={onToggle}
          basePath={basePath}
        />
      ))}
    </ul>
  )
}
