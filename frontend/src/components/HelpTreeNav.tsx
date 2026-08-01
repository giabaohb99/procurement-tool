import { Link } from 'react-router-dom'

import type { HelpNode } from '../utils/help-tree'

// Cây thư mục bài viết ở sidebar HDSD. Node có con = thư mục (bấm mũi tên để mở/đóng),
// node lá = bài viết. Cả hai đều điều hướng sang /hdsd/:id.

interface TreeNodeProps {
  node: HelpNode
  activeId: number | null
  expanded: Set<number>
  onToggle: (id: number) => void
  level?: number
}

function TreeNode({ node, activeId, expanded, onToggle, level = 0 }: TreeNodeProps) {
  const isFolder = !!node.children?.length
  const isExpanded = expanded.has(node.id)
  const isActive = activeId === node.id

  return (
    <li>
      <Link
        to={`/hdsd/${node.id}`}
        className={'hc-node-link' + (isActive ? ' active' : '')}
        style={{ marginLeft: level * 16 }}
        onClick={() => { if (isFolder && !isExpanded) onToggle(node.id) }}
      >
        {isFolder ? (
          <span
            className={'hc-node-caret' + (isExpanded ? ' open' : '')}
            role="button"
            aria-label={isExpanded ? 'Thu gọn' : 'Mở rộng'}
            onClick={(e) => { e.preventDefault(); e.stopPropagation(); onToggle(node.id) }}
          >
            <i className="ti ti-caret-right-filled" style={{ fontSize: 12 }} />
          </span>
        ) : (
          <span style={{ width: 24, flexShrink: 0 }} />
        )}
        <span className="hc-node-text">{node.title}</span>
      </Link>

      {isFolder && isExpanded && (
        <ul className="hc-submenu-children">
          {node.children!.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              activeId={activeId}
              expanded={expanded}
              onToggle={onToggle}
              level={level + 1}
            />
          ))}
        </ul>
      )}
    </li>
  )
}

interface HelpTreeNavProps {
  tree: HelpNode[]
  activeId: number | null
  expanded: Set<number>
  onToggle: (id: number) => void
}

export default function HelpTreeNav({ tree, activeId, expanded, onToggle }: HelpTreeNavProps) {
  if (tree.length === 0) {
    return (
      <div style={{ padding: '1rem', color: 'var(--muted)', fontSize: 13.5, textAlign: 'center' }}>
        Chưa có nội dung
      </div>
    )
  }

  return (
    <ul className="hc-menu-root">
      {tree.map((node) => (
        <TreeNode
          key={node.id}
          node={node}
          activeId={activeId}
          expanded={expanded}
          onToggle={onToggle}
        />
      ))}
    </ul>
  )
}
