import { useCallback, useState } from 'react'

import { dropArticle } from '@/lib/help-article-actions'
import type { HelpNode } from '@/lib/help-tree'
import {
  canDrop, depthOf, MAX_DEPTH, positionFromPointer, type DropTarget,
} from '@/lib/help-tree-dnd'

// Trạng thái kéo-thả cây bài viết, dùng chung cho bảng cây /admin và sidebar khu quản trị.
// Logic thuần (vị trí thả, nước thả hợp lệ) nằm ở lib/help-tree-dnd.ts; ghi xuống server ở
// dropArticle. Ở đây chỉ giữ state + các handler DOM.

/** Bộ điều khiển kéo-thả cấp xuống từng dòng; null = đang tắt (vd bảng cây đang lọc). */
export interface TreeDnd {
  dragId: number | null
  target: DropTarget | null
  onDragStart: (id: number) => void
  onDragOver: (e: React.DragEvent, node: HelpNode) => void
  onDrop: (e: React.DragEvent, node: HelpNode) => void
  onDragEnd: () => void
}

export function useHelpTreeDnd({
  tree, enabled = true, onChanged, onDroppedInside,
}: {
  /** Cây ĐẦY ĐỦ — thứ tự mới được tính trên cây này, không phải trên danh sách đang hiển thị. */
  tree: HelpNode[]
  enabled?: boolean
  onChanged: () => Promise<void> | void
  /** Gọi khi thả VÀO TRONG một mục — nơi gọi thường mở sẵn mục đó để thấy ngay kết quả. */
  onDroppedInside?: (parentId: number) => void
}): TreeDnd | null {
  const [dragId, setDragId] = useState<number | null>(null)
  const [target, setTarget] = useState<DropTarget | null>(null)

  const reset = useCallback(() => {
    setDragId(null)
    setTarget(null)
  }, [])

  const onDragOver = useCallback((e: React.DragEvent, node: HelpNode) => {
    if (dragId === null) return
    // Chỉ gợi ý "thả vào trong" khi mục đích còn chỗ chứa con (cây tối đa 3 cấp)
    const allowInside = depthOf(tree, node.id) < MAX_DEPTH
    const position = positionFromPointer(
      e.currentTarget.getBoundingClientRect(), e.clientY, allowInside,
    )

    if (!canDrop(tree, dragId, node.id, position)) {
      setTarget(null)
      return
    }
    // preventDefault mới cho phép thả — không gọi thì trình duyệt từ chối drop
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    setTarget((prev) =>
      prev?.id === node.id && prev.position === position ? prev : { id: node.id, position })
  }, [dragId, tree])

  const onDrop = useCallback(async (e: React.DragEvent, node: HelpNode) => {
    e.preventDefault()
    const dropped = target
    const id = dragId
    reset()
    if (id === null || dropped?.id !== node.id) return

    if (await dropArticle(tree, id, node.id, dropped.position)) {
      if (dropped.position === 'inside') onDroppedInside?.(node.id)
      await onChanged()
    }
  }, [dragId, target, tree, onChanged, onDroppedInside, reset])

  if (!enabled) return null

  return { dragId, target, onDragStart: setDragId, onDragOver, onDrop, onDragEnd: reset }
}
