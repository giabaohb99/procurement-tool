import { useRef } from 'react'
import { Link } from 'react-router-dom'
import { ChevronRight, FileText, Folder, FolderOpen } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import type { HelpNode } from '@/lib/help-tree'
import type { TreeDnd } from '@/lib/use-help-tree-dnd'
import { cn } from '@/lib/utils'

// Một dòng trong danh sách "Bài viết liên quan" ở sidebar khu quản trị.
// Có bài con thì bấm mũi tên để SỔ XUỐNG xem ngay tại đây, khỏi phải mở từng bài mới biết
// bên trong có gì. Nhánh chứa bài đang mở được bung sẵn (xem admin-sidebar-nav).
// Kéo-thả đổi mục cha / thứ tự giống hệt bảng cây /admin (dùng chung useHelpTreeDnd):
// mép trên/dưới = chèn trước/sau cùng cấp, giữa dòng = chuyển vào trong làm bài con.

export default function AdminSidebarTreeItem({
  node, activeId, isOpen: isOpenOf, onToggle, dnd, depth = 0,
}: {
  node: HelpNode
  activeId: number | null
  /** Nhánh nào đang bung — do bên gọi quyết định (mặc định theo bài đang mở + ghi đè tay). */
  isOpen: (id: number) => boolean
  onToggle: (id: number) => void
  dnd: TreeDnd | null
  depth?: number
}) {
  const rowRef = useRef<HTMLDivElement>(null)
  const children = node.children || []
  const hasChildren = children.length > 0
  const isOpen = isOpenOf(node.id)
  const isActive = node.id === activeId

  const isDragging = dnd?.dragId === node.id
  const drop = dnd?.target?.id === node.id ? dnd.target.position : null

  return (
    <li>
      <div
        ref={rowRef}
        draggable={!!dnd}
        onDragStart={dnd ? (e) => {
          e.dataTransfer.effectAllowed = 'move'
          // dataTransfer phải có dữ liệu thì Firefox mới bắt đầu kéo
          e.dataTransfer.setData('text/plain', String(node.id))
          if (rowRef.current) e.dataTransfer.setDragImage(rowRef.current, 16, 16)
          dnd.onDragStart(node.id)
        } : undefined}
        onDragOver={dnd ? (e) => dnd.onDragOver(e, node) : undefined}
        onDrop={dnd ? (e) => dnd.onDrop(e, node) : undefined}
        onDragEnd={dnd?.onDragEnd}
        className={cn(
          'relative flex items-center rounded-md',
          dnd && 'cursor-grab active:cursor-grabbing',
          isDragging && 'opacity-40',
          // Vạch chỉ chỗ chèn khi thả cùng cấp; nền + viền khi thả VÀO TRONG thành bài con
          drop === 'before' && 'before:absolute before:inset-x-0 before:top-0 before:h-0.5 before:bg-primary',
          drop === 'after' && 'after:absolute after:inset-x-0 after:bottom-0 after:h-0.5 after:bg-primary',
          drop === 'inside' && 'bg-primary/8 ring-2 ring-inset ring-primary',
        )}
        style={{ paddingLeft: depth * 12 }}
      >
        {hasChildren ? (
          <button
            type="button"
            aria-label={isOpen ? `Thu gọn ${node.title}` : `Mở rộng ${node.title}`}
            aria-expanded={isOpen}
            onClick={() => onToggle(node.id)}
            className="grid size-5 shrink-0 place-items-center rounded-sm text-muted-foreground transition-colors hover:bg-border hover:text-navy"
          >
            <ChevronRight className={cn('size-3.5 transition-transform', isOpen && 'rotate-90')} />
          </button>
        ) : (
          // Giữ chỗ đúng bằng nút mũi tên để tiêu đề các dòng thẳng hàng nhau
          <span aria-hidden className="size-5 shrink-0" />
        )}

        <Link
          to={`/admin/${node.id}`}
          // Thẻ <a> mặc định tự kéo được (kéo ra thành link) — tắt đi để cú kéo thuộc về
          // dòng bao ngoài, nếu không dataTransfer sẽ là link chứ không phải bài viết
          draggable={false}
          className={cn(
            'flex min-w-0 flex-1 items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors',
            isActive
              ? 'bg-accent font-semibold text-accent-foreground'
              : 'text-navy hover:bg-secondary',
          )}
        >
          {hasChildren
            ? (isOpen
                ? <FolderOpen className="size-4 shrink-0 text-primary" strokeWidth={1.75} />
                : <Folder className="size-4 shrink-0 text-primary" strokeWidth={1.75} />)
            : <FileText className="size-4 shrink-0 text-muted-foreground" strokeWidth={1.75} />}
          <span className="min-w-0 flex-1 truncate">{node.title}</span>
          {hasChildren && (
            <Badge variant="outline" className="shrink-0 px-1.5 font-normal text-muted-foreground">
              {children.length}
            </Badge>
          )}
        </Link>
      </div>

      {hasChildren && isOpen && (
        <ul className="mt-0.5 space-y-0.5">
          {children.map((child) => (
            <AdminSidebarTreeItem
              key={child.id}
              node={child}
              activeId={activeId}
              isOpen={isOpenOf}
              onToggle={onToggle}
              dnd={dnd}
              depth={depth + 1}
            />
          ))}
        </ul>
      )}
    </li>
  )
}
