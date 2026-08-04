import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ChevronDown, ChevronRight, ChevronUp, FilePlus2, FileText, Folder, FolderInput, FolderOpen,
  MoreHorizontal, Pencil, SquareArrowOutUpRight, Trash2,
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
import { cn } from '@/lib/utils'

// Bảng cây quản lý bài viết ở /admin — 3 cấp: Mục gốc > Bài viết > Bài chi tiết.
// Mỗi dòng có thao tác: mở, thêm bài con, đổi tên, đổi thứ tự, xóa.

/** Cấp sâu nhất được phép tạo con (0-based) — cấp 2 là bài chi tiết, không thêm con nữa. */
const MAX_DEPTH = 2

interface TreeTableProps {
  tree: HelpNode[]
  onChanged: () => Promise<void> | void
  /** Lọc theo tiêu đề (không dấu, chữ thường) — rỗng = hiện tất cả. */
  filter?: string
}

/** Bỏ dấu + chữ thường để lọc theo kiểu gõ không dấu. */
function fold(text: string): string {
  return text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[đĐ]/g, 'd').toLowerCase()
}

/** Giữ lại nhánh có node khớp từ khóa (giữ cả cha để không mất ngữ cảnh). */
function filterTree(nodes: HelpNode[], kw: string): HelpNode[] {
  return nodes.reduce<HelpNode[]>((acc, node) => {
    const children = filterTree(node.children || [], kw)
    if (fold(node.title).includes(kw) || children.length) {
      acc.push({ ...node, children })
    }
    return acc
  }, [])
}

export default function HelpArticleTreeTable({ tree, onChanged, filter = '' }: TreeTableProps) {
  const [expanded, setExpanded] = useState<Set<number>>(new Set())

  const kw = fold(filter.trim())
  const shown = kw ? filterTree(tree, kw) : tree

  const toggle = (id: number) =>
    setExpanded((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })

  if (shown.length === 0) {
    return (
      <div className="rounded-md border border-dashed px-6 py-12 text-center">
        <FileText className="mx-auto mb-2 size-8 text-muted-foreground" strokeWidth={1.5} />
        <strong className="block text-navy">
          {kw ? 'Không tìm thấy bài viết khớp từ khóa' : 'Chưa có tài liệu nào'}
        </strong>
        <span className="text-sm text-muted-foreground">
          {kw ? 'Thử từ khóa khác.' : 'Bấm "Thêm mục gốc" để tạo bài viết đầu tiên.'}
        </span>
      </div>
    )
  }

  return (
    <div className="overflow-hidden rounded-md border">
      <div className="flex items-center gap-3 border-b bg-secondary px-4 py-2.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        <span className="flex-1">Tiêu đề</span>
        <span className="w-28 shrink-0">Cấp</span>
        <span className="w-20 shrink-0 text-right">Bài con</span>
        <span className="w-[6.5rem] shrink-0" />
      </div>

      <ul>
        {shown.map((node, index) => (
          <TreeRow
            key={node.id}
            node={node}
            siblings={shown}
            index={index}
            depth={0}
            tree={tree}
            expanded={kw ? null : expanded}
            onToggle={toggle}
            onChanged={onChanged}
          />
        ))}
      </ul>
    </div>
  )
}

interface TreeRowProps {
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
}

function TreeRow({ node, siblings, index, depth, tree, expanded, onToggle, onChanged }: TreeRowProps) {
  const [moveOpen, setMoveOpen] = useState(false)
  const children = node.children || []
  const hasChildren = children.length > 0
  const isOpen = expanded === null ? true : expanded.has(node.id)
  const canAddChild = depth < MAX_DEPTH

  const run = async (fn: () => Promise<boolean | number | null>) => {
    const changed = await fn()
    if (changed) await onChanged()
  }

  return (
    <li className="border-b last:border-b-0">
      <div className="flex items-center gap-3 px-4 py-2.5 transition-colors hover:bg-secondary/60">
        <div className="flex min-w-0 flex-1 items-center gap-1.5" style={{ paddingLeft: depth * 22 }}>
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
            />
          ))}
        </ul>
      )}
    </li>
  )
}
