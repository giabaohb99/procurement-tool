import type { DragEvent } from 'react'

import { useTreeRowDropZone } from './use-tree-row-drop-zone'
import { useTreeRowExternalDrop } from './use-tree-row-external-drop'
import type { DropZone } from './resolve-drop-zone'
import type { FlatTreeNode, TreeNode } from './tree-types'

interface UseTreeRowDndOptions<T> {
  node: TreeNode<T>
  row: FlatTreeNode<T>
  draggable: boolean
  drop: 'valid' | 'invalid' | undefined
  reorderable: boolean
  externalDropMimeType?: string
  acceptsExternalDrop?: (node: TreeNode<T>) => boolean
  onDragStartNode?: (node: TreeNode<T>) => void
  onDragStartEvent?: (node: TreeNode<T>, event: DragEvent<HTMLDivElement>) => void
  onDragEndNode?: () => void
  onDropNode?: (node: TreeNode<T>) => void
  onReorderDrop?: (node: TreeNode<T>, position: 'before' | 'after') => void
  onExternalDropNode?: (node: TreeNode<T>, event: DragEvent<HTMLDivElement>) => void
}

/**
 * Toàn bộ SỰ KIỆN kéo thả (`drag*`/`drop`) của MỘT dòng cây — nội bộ
 * (`useTreeRowDropZone`) lẫn payload ngoài cây (`useTreeRowExternalDrop`).
 * Tách khỏi `tree-row.tsx` (thuần JSX) để tệp đó giữ dưới 200 dòng.
 */
export function useTreeRowDnd<T>({
  node,
  row,
  draggable,
  drop,
  reorderable,
  externalDropMimeType,
  acceptsExternalDrop,
  onDragStartNode,
  onDragStartEvent,
  onDragEndNode,
  onDropNode,
  onReorderDrop,
  onExternalDropNode,
}: UseTreeRowDndOptions<T>) {
  const { dropPossible, hoverZone, setHoverZone, resolveZone } = useTreeRowDropZone(
    drop !== undefined,
    drop === 'valid',
    reorderable,
  )
  const externalDrop = useTreeRowExternalDrop(
    externalDropMimeType,
    acceptsExternalDrop ? acceptsExternalDrop(node) : true,
  )

  function resolveZoneAt(event: { currentTarget: HTMLElement; clientY: number }): DropZone | null {
    return resolveZone(event)
  }

  return {
    hoverZone,
    externalHover: externalDrop.hover,
    dragHandlers: {
      //  Firefox bỏ qua `dragstart` nếu không gọi `setData` — nội dung không
      //  quan trọng, `onDragStartNode` mới là nguồn sự thật.
      onDragStart: (event: DragEvent<HTMLDivElement>) => {
        if (!draggable) return
        event.dataTransfer?.setData('text/plain', String(row.id))
        onDragStartNode?.(node)
        onDragStartEvent?.(node, event)
      },
      onDragEnd: () => {
        setHoverZone(null)
        externalDrop.setHover(false)
        onDragEndNode?.()
      },
      //  Không `preventDefault` thì trình duyệt từ chối `drop` mặc định.
      onDragOver: (event: DragEvent<HTMLDivElement>) => {
        if (externalDrop.isPayload(event)) {
          event.preventDefault()
          externalDrop.setHover(true)
          return
        }
        if (!dropPossible) return
        event.preventDefault()
        setHoverZone(resolveZoneAt(event))
      },
      //  Rời sang một PHẦN TỬ CON của chính dòng (icon, nhãn…) không phải rời
      //  dòng — chặn ở đây để chỉ báo khỏi nhấp nháy theo con.
      onDragLeave: (event: DragEvent<HTMLDivElement>) => {
        if (event.currentTarget.contains(event.relatedTarget as Node | null)) return
        setHoverZone(null)
        externalDrop.setHover(false)
      },
      //  Tính vùng thả NGAY LÚC THẢ, không đọc lại `hoverZone`: bài kiểm cũ bắn
      //  thẳng `drop` mà không bắn `dragover` trước.
      onDrop: (event: DragEvent<HTMLDivElement>) => {
        if (externalDrop.isPayload(event)) {
          event.preventDefault()
          externalDrop.setHover(false)
          onExternalDropNode?.(node, event)
          return
        }
        event.preventDefault()
        const zone = resolveZoneAt(event)
        setHoverZone(null)
        if (zone === 'into') onDropNode?.(node)
        else if (zone === 'before' || zone === 'after') onReorderDrop?.(node, zone)
      },
    },
  }
}
