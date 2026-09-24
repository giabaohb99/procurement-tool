import type { DragEvent } from 'react'

import type { TreeNode } from '@/shared/tree/tree-types'
import { FOLDER_DRAG_MIME, writeFolderDragPayload } from '../helpers/folder-drag-payload'
import { parseDocumentLeafId } from '../helpers/folder-tree-document-leaf-id'
import type { DocFolderTreeNode } from '../types/document-folder'
import type { useFolderDragMove } from './use-folder-drag-move'

/**
 * Gộp kéo-thả-ĐỔI-CHA của THƯ MỤC (`useFolderDragMove`, đã có) với kéo LÁ VĂN
 * BẢN ra khỏi cây (ghi payload liên khung, `folder-drag-payload.ts`) thành
 * MỘT bộ props sẵn sàng spread vào `TreeView` — hai việc ĐỘC LẬP (lá không
 * đổi cha; thư mục không ghi MIME liên khung) nhưng dùng CHUNG đúng ba prop
 * `canDrag`/`onDragStartNode`/`onDragStartEvent` của `TreeView`, nên phải hợp
 * nhất ở MỘT chỗ thay vì để `folder-tree-panel.tsx` tự rẽ nhánh (tệp đó đã sát
 * 200 dòng).
 */
export function useFolderTreeDrag(drag: ReturnType<typeof useFolderDragMove>) {
  function canDrag(node: TreeNode<DocFolderTreeNode>) {
    return Boolean(parseDocumentLeafId(node.id)) || drag.canDrag(node)
  }

  function onDragStartNode(node: TreeNode<DocFolderTreeNode>) {
    //  Lá văn bản KHÔNG đi qua `useFolderDragMove` — nó không đổi cha, chỉ
    //  ghi payload liên khung ở `onDragStartEvent` bên dưới.
    if (!parseDocumentLeafId(node.id)) drag.onDragStartNode(node)
  }

  function onDragStartEvent(node: TreeNode<DocFolderTreeNode>, event: DragEvent<HTMLDivElement>) {
    const parsed = parseDocumentLeafId(node.id)
    if (!parsed) return
    event.dataTransfer.effectAllowed = 'copyMove'
    writeFolderDragPayload(event.dataTransfer, {
      documentIds: [parsed.documentId],
      folderIds: [],
      sourceFolderId: parsed.folderId,
    })
  }

  return {
    canDrag,
    onDragStartNode,
    onDragStartEvent,
    onDragEndNode: drag.onDragEndNode,
    dropState: drag.dropState,
    onDropNode: drag.onDropNode,
    canReorderWith: drag.canReorderWith,
    onReorderDrop: drag.onReorderDrop,
    externalDropMimeType: FOLDER_DRAG_MIME,
    acceptsExternalDrop: drag.acceptsExternalDrop,
    onExternalDropNode: drag.onExternalDropNode,
  }
}
