import { useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ChevronDown, ChevronRight, ChevronUp, FilePlus2, FileText, Folder, FolderInput, FolderOpen,
  GripVertical, MoreHorizontal, Pencil, SquareArrowOutUpRight, Trash2,
} from 'lucide-react'

import MoveArticleDialog from '@/components/move-article-dialog'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  createArticle, deleteArticle, levelLabel, renameArticle, reorderSibling,
} from '@/lib/help-article-actions'
import type { HelpNode } from '@/lib/help-tree'
import { MAX_DEPTH, type DropTarget } from '@/lib/help-tree-dnd'
import { cn } from '@/lib/utils'

// Một dòng của bảng cây /admin — mở, thêm bài con, đổi tên, đổi thứ tự, xóa,
// và kéo-thả (đổi thứ tự / chuyển sang mục cha khác).

/** Bộ điều khiển kéo-thả do bảng cây cấp xuống; null = đang lọc nên tắt kéo-thả. */
export interface TreeDnd {
  dragId: number | null
  target: DropTarget | null
  onDragStart: (id: number) => void
  onDragOver: (e: React.DragEvent, node: HelpNode) => void
  onDrop: (e: React.DragEvent, node: HelpNode) => void
  onDragEnd: () => void
}

export interface TreeRowProps {
  node: HelpNode
  siblings: HelpNode[]
  index: number
  depth: number
  /** Cây ĐẦY ĐỦ (không lọc) — hộp thoại chuyển bài cần để liệt kê thư mục cha hợp lệ. */
  tree: HelpNode[]
  /** null = đang lọc, mở hết mọi nhánh. */
  expanded: Set<number> | null
  onToggle: (id: number) => void
  onChanged: () => Promise<void> | void
  dnd: TreeDnd | null
}

export default function TreeRow({
  node, siblings, index, depth, tree, expanded, onToggle, onChanged, dnd,
}: TreeRowProps) {
  const [moveOpen, setMoveOpen] = useState(false)
  const rowRef = useRef<HTMLDivElement>(null)

  const children = node.children || []
  const hasChildren = children.length > 0
  const isOpen = expanded === null ? true : expanded.has(node.id)
  const canAddChild = depth < MAX_DEPTH

  const isDragging = dnd?.dragId === node.id
  const drop = dnd?.target?.id === node.id ? dnd.target.position : null

  const run = async (fn: () => Promise<boolean | number | null>) => {
    const changed = await fn()
    if (changed) await onChanged()
  }

  return (
    <li className="border-b last:border-b-0">
      <div
        ref={rowRef}
        onDragOver={dnd ? (e) => dnd.onDragOver(e, node) : undefined}
        onDrop={dnd ? (e) => dnd.onDrop(e, node) : undefined}
        className={cn(
          'relative flex items-center gap-3 px-4 py-2.5 transition-colors hover:bg-secondary/60',
          isDragging && 'opacity-40',
          // Vạch chỉ chỗ chèn khi thả cùng cấp; nền + viền khi thả VÀO TRONG thành bài con
          drop === 'before' && 'before:absolute before:inset-x-0 before:top-0 before:h-0.5 before:bg-primary',
          drop === 'after' && 'after:absolute after:inset-x-0 after:bottom-0 after:h-0.5 after:bg-primary',
          drop === 'inside' && 'bg-primary/8 ring-2 ring-inset ring-primary',
        )}
      >
        <div className="flex min-w-0 flex-1 items-center gap-1.5" style={{ paddingLeft: depth * 22 }}>
          {dnd && (
            <button
              type="button"
              draggable
              aria-label={`Kéo để sắp xếp: ${node.title}`}
              title="Kéo để đổi thứ tự hoặc chuyển sang mục khác"
              onDragStart={(e) => {
                e.dataTransfer.effectAllowed = 'move'
                // dataTransfer phải có dữ liệu thì Firefox mới bắt đầu kéo
                e.dataTransfer.setData('text/plain', String(node.id))
                if (rowRef.current) e.dataTransfer.setDragImage(rowRef.current, 16, 16)
                dnd.onDragStart(node.id)
              }}
              onDragEnd={dnd.onDragEnd}
              className="grid size-5 shrink-0 cursor-grab place-items-center rounded-sm text-muted-foreground/60 hover:bg-border hover:text-muted-foreground active:cursor-grabbing"
            >
              <GripVertical className="size-3.5" />
            </button>
          )}

          {hasChildren ? (
            <button
              type="button"
              onClick={() => onToggle(node.id)}
              aria-label={isOpen ? 'Thu gọn' : 'Mở rộng'}
              className="grid size-5 shrink-0 place-items-center rounded-sm text-muted-foreground hover:bg-border"
            >
              {isOpen ? <ChevronDown className="size-4" /> : <ChevronRight className="size-4" />}
            </button>
          ) : (
            <span className="w-5 shrink-0" />
          )}

          {hasChildren
            ? (isOpen
                ? <FolderOpen className="size-4 shrink-0 text-primary" strokeWidth={1.75} />
                : <Folder className="size-4 shrink-0 text-primary" strokeWidth={1.75} />)
            : <FileText className="size-4 shrink-0 text-muted-foreground" strokeWidth={1.75} />}

          <Link
            to={`/admin/${node.id}`}
            className={cn(
              'truncate text-sm text-navy hover:text-primary hover:underline',
              depth === 0 && 'font-semibold',
            )}
          >
            {node.title}
          </Link>
        </div>

        <span className="w-28 shrink-0">
          <Badge variant="outline" className="font-normal text-muted-foreground">
            {levelLabel(depth)}
          </Badge>
        </span>

        <span className="w-20 shrink-0 text-right text-sm text-muted-foreground">
          {hasChildren ? children.length : '—'}
        </span>

        <div className="flex w-[6.5rem] shrink-0 items-center justify-end gap-0.5">
          <Button
            variant="ghost" size="icon" className="size-7" title="Lên"
            disabled={index === 0}
            onClick={() => run(() => reorderSibling(siblings, index, -1))}
          >
            <ChevronUp className="size-4" />
          </Button>
          <Button
            variant="ghost" size="icon" className="size-7" title="Xuống"
            disabled={index === siblings.length - 1}
            onClick={() => run(() => reorderSibling(siblings, index, 1))}
          >
            <ChevronDown className="size-4" />
          </Button>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="size-7" title="Thao tác khác">
                <MoreHorizontal className="size-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-52">
              <DropdownMenuItem asChild>
                <Link to={`/admin/${node.id}`}>
                  <SquareArrowOutUpRight /> Mở bài viết
                </Link>
              </DropdownMenuItem>
              {canAddChild && (
                <DropdownMenuItem
                  onClick={() => run(() => createArticle(node.id, children.length, depth + 1))}
                >
                  <FilePlus2 /> Thêm {levelLabel(depth + 1).toLowerCase()}
                </DropdownMenuItem>
              )}
              <DropdownMenuItem onClick={() => run(() => renameArticle(node))}>
                <Pencil /> Đổi tiêu đề
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setMoveOpen(true)}>
                <FolderInput /> Chuyển sang mục khác
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem variant="destructive" onClick={() => run(() => deleteArticle(node))}>
                <Trash2 /> Xóa
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      <MoveArticleDialog
        tree={tree}
        node={node}
        open={moveOpen}
        onOpenChange={setMoveOpen}
        onMoved={onChanged}
      />

      {hasChildren && isOpen && (
        <ul className="border-t bg-secondary/30">
          {children.map((child, i) => (
            <TreeRow
              key={child.id}
              node={child}
              siblings={children}
              index={i}
              depth={depth + 1}
              tree={tree}
              expanded={expanded}
              onToggle={onToggle}
              onChanged={onChanged}
              dnd={dnd}
            />
          ))}
        </ul>
      )}
    </li>
  )
}
