import { useCallback, useState } from 'react'
import { FileText } from 'lucide-react'

import TreeRow, { type TreeDnd } from '@/components/help-article-tree-row'
import { dropArticle } from '@/lib/help-article-actions'
import type { HelpNode } from '@/lib/help-tree'
import {
  canDrop, depthOf, MAX_DEPTH, positionFromPointer, type DropTarget,
} from '@/lib/help-tree-dnd'

// Bảng cây quản lý bài viết ở /admin — 3 cấp: Mục gốc > Bài viết > Bài chi tiết.
// File này giữ khung bảng + trạng thái kéo-thả; phần hiển thị 1 dòng nằm ở help-article-tree-row.
// Kéo-thả bị TẮT khi đang lọc: danh sách hiển thị lúc đó là cây đã cắt bớt,
// tính lại thứ tự trên đó sẽ ghi sai sort_order của các bài bị ẩn.

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
  const [dragId, setDragId] = useState<number | null>(null)
  const [dropTarget, setDropTarget] = useState<DropTarget | null>(null)

  const kw = fold(filter.trim())
  const shown = kw ? filterTree(tree, kw) : tree

  const toggle = useCallback((id: number) =>
    setExpanded((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    }), [])

  const resetDrag = useCallback(() => {
    setDragId(null)
    setDropTarget(null)
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent, node: HelpNode) => {
    if (dragId === null) return
    // Chỉ gợi ý "thả vào trong" khi mục đích còn chỗ chứa con (cây tối đa 3 cấp)
    const allowInside = depthOf(tree, node.id) < MAX_DEPTH
    const position = positionFromPointer(e.currentTarget.getBoundingClientRect(), e.clientY, allowInside)

    if (!canDrop(tree, dragId, node.id, position)) {
      setDropTarget(null)
      return
    }
    // preventDefault mới cho phép thả — không gọi thì trình duyệt từ chối drop
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    setDropTarget((prev) =>
      prev?.id === node.id && prev.position === position ? prev : { id: node.id, position })
  }, [dragId, tree])

  const handleDrop = useCallback(async (e: React.DragEvent, node: HelpNode) => {
    e.preventDefault()
    const target = dropTarget
    const id = dragId
    resetDrag()
    if (id === null || target?.id !== node.id) return

    if (await dropArticle(tree, id, node.id, target.position)) {
      // Mở sẵn mục vừa nhận bài để thấy ngay kết quả
      if (target.position === 'inside') setExpanded((prev) => new Set(prev).add(node.id))
      await onChanged()
    }
  }, [dragId, dropTarget, tree, onChanged, resetDrag])

  const dnd: TreeDnd | null = kw ? null : {
    dragId,
    target: dropTarget,
    onDragStart: setDragId,
    onDragOver: handleDragOver,
    onDrop: handleDrop,
    onDragEnd: resetDrag,
  }

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
    <>
      <p className="mb-2 text-xs text-muted-foreground">
        {kw
          ? 'Đang lọc — xóa từ khóa để kéo-thả sắp xếp lại.'
          : 'Kéo biểu tượng ⠿ để đổi thứ tự; thả vào GIỮA một mục để chuyển bài vào trong mục đó.'}
      </p>

      {/* KHÔNG gắn onDragLeave ở đây: sự kiện bubble từ từng dòng con, rê qua dòng khác
          sẽ xóa mất trạng thái đang kéo. Việc dọn trạng thái do onDragEnd của tay cầm lo. */}
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
              dnd={dnd}
            />
          ))}
        </ul>
      </div>
    </>
  )
}
