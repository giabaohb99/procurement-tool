import { useMemo, useState, type DragEvent } from 'react'

import type { TreeNode } from '@/shared/tree/tree-types'
import {
  deepestDescendantDepth,
  isValidFolderDropTarget,
  isValidFolderReorderTarget,
  reorderSiblingIds,
} from '../helpers/folder-drop-target'
import {
  FOLDER_DRAG_MIME,
  hasFolderDragPayload,
  readFolderDragPayload,
} from '../helpers/folder-drag-payload'
import {
  useLinkDocumentsToFolder,
  useMoveDocFolder,
  useReorderDocFolders,
  useUnlinkDocumentsFromFolder,
} from './use-document-folders'
import { FOLDER_ACCESS_LEVEL, FOLDER_KIND, FOLDER_LINK_MODE } from '../types/document-folder'
import type { DocFolderTreeNode } from '../types/document-folder'
import { NEW_FOLDER_TEMP_ID, ROOT_PARENT_ID } from '../helpers/insert-temp-tree-node'

/** Thả hợp lệ nhưng nhánh đang kéo có văn bản — chờ người dùng xác nhận trước khi gọi API. */
export interface PendingFolderDrop {
  source: DocFolderTreeNode
  targetId: number
}

/**
 * KÉO THẢ đổi cha trên cây — dồn hết state + tính hợp lệ của một lượt kéo vào
 * một hook, để `folder-tree-panel.tsx` chỉ còn gắn bốn hàm này thẳng vào
 * props tương ứng của `TreeView` (`canDrag`/`onDragStartNode`/`dropState`/
 * `onDropNode`).
 */
export function useFolderDragMove(rows: DocFolderTreeNode[] | undefined) {
  const [dragSourceId, setDragSourceId] = useState<number | null>(null)
  //  Thả vào một nhánh có văn bản (kể cả văn bản mình không xem được) phải hỏi
  //  lại trước — cùng luật với «Chuyển tới…» (`folder-move-dialog.tsx`), chỉ
  //  khác đường vào là kéo thả thay vì mở hộp thoại chọn cây.
  const [pendingDrop, setPendingDrop] = useState<PendingFolderDrop | null>(null)
  const moveFolder = useMoveDocFolder()
  const reorderFolders = useReorderDocFolders()
  const linkDocuments = useLinkDocumentsToFolder()
  const unlinkDocuments = useUnlinkDocumentsFromFolder()

  const dragSource = useMemo(() => {
    if (dragSourceId == null || !rows) return null
    const node = rows.find((row) => row.id === dragSourceId)
    if (!node) return null
    return {
      id: node.id,
      parentId: node.parent_id,
      path: node.path,
      depth: node.depth,
      deepestDescendantDepth: deepestDescendantDepth(rows, node),
    }
  }, [dragSourceId, rows])

  function canDrag(node: TreeNode<DocFolderTreeNode>) {
    return Boolean(
      //  Thư mục pháp nhân kéo được như mọi thư mục (mở 24/09/2026); riêng
      //  nhóm «Công ty» luôn đứng ở gốc — backend cũng chặn chuyển nó.
      node.data &&
      node.data.kind !== FOLDER_KIND.companyGroup &&
      node.data.my_level >= FOLDER_ACCESS_LEVEL.manage,
    )
  }

  function dropState(node: TreeNode<DocFolderTreeNode>): 'valid' | 'invalid' | undefined {
    if (!dragSource || !node.data) return undefined
    if (node.data.id === dragSource.id) return undefined
    return isValidFolderDropTarget(dragSource, {
      id: node.data.id,
      path: node.data.path,
      depth: node.data.depth,
      myLevel: node.data.my_level,
    })
      ? 'valid'
      : 'invalid'
  }

  function onDropNode(node: TreeNode<DocFolderTreeNode>) {
    if (dragSourceId == null) return
    const targetId = Number(node.id)
    const sourceRow = rows?.find((row) => row.id === dragSourceId)
    setDragSourceId(null)
    if (sourceRow && sourceRow.document_count_branch > 0) {
      setPendingDrop({ source: sourceRow, targetId })
      return
    }
    moveFolder.mutate({ id: dragSourceId, newParentId: targetId })
  }

  /**
   * Đích cho ĐỔI THỨ TỰ (thả trước/sau, cùng cha) — luật khác hẳn
   * `dropState`/đổi cha: cần quyền QUẢN LÝ trên CHA CHUNG (không phải trên
   * chính dòng đích), xem `isValidFolderReorderTarget`.
   */
  function canReorderWith(node: TreeNode<DocFolderTreeNode>): boolean {
    if (!dragSource || !node.data || !rows) return false
    if (node.data.id === dragSource.id) return false
    const parent = rows.find((row) => row.id === node.data?.parent_id)
    if (!parent) return false
    return isValidFolderReorderTarget(
      { id: dragSource.id, parentId: dragSource.parentId },
      { id: node.data.id, parentId: node.data.parent_id, parentMyLevel: parent.my_level },
    )
  }

  /**
   * Thả trước/sau một anh em — đánh số lại `sort_order` cho CẢ tập anh em
   * cùng cha theo chỉ số mảng mới (`reorderSiblingIds`), không chỉ hai dòng
   * vừa đổi: backend nhận `sort_order` là số thật, gửi thiếu phần còn lại thì
   * không có cách nào "chen" đúng số giữa hai giá trị nguyên liền kề.
   */
  function onReorderDrop(node: TreeNode<DocFolderTreeNode>, position: 'before' | 'after') {
    const sourceId = dragSourceId
    setDragSourceId(null)
    if (sourceId == null || !rows) return
    const targetId = Number(node.id)
    const sourceRow = rows.find((row) => row.id === sourceId)
    const targetRow = rows.find((row) => row.id === targetId)
    if (!sourceRow || !targetRow || sourceRow.parent_id !== targetRow.parent_id) return

    const siblingIds = rows
      .filter((row) => row.parent_id === sourceRow.parent_id)
      .sort((a, b) => a.sort_order - b.sort_order || a.name.localeCompare(b.name, 'vi'))
      .map((row) => row.id)
    const nextOrder = reorderSiblingIds(siblingIds, sourceId, targetId, position)
    reorderFolders.mutate(nextOrder.map((id, index) => ({ id, sort_order: index })))
  }

  function confirmPendingDrop() {
    if (!pendingDrop) return
    moveFolder.mutate({ id: pendingDrop.source.id, newParentId: pendingDrop.targetId })
    setPendingDrop(null)
  }

  /**
   * Nút GỐC («THƯ MỤC» ở đầu cây) nhận thả = đưa thư mục ra GỐC cây (lỗi báo
   * 24/09/2026: kéo thư mục con ra gốc không có chỗ nào để thả). Nhận cả lượt
   * kéo TRONG cây (`dragSource`) lẫn lượt kéo từ khung phải (payload). Thư mục
   * đã nằm ở gốc thì không nhận — thả vào là không đổi gì.
   */
  function canDropOnRoot(event: DragEvent<HTMLElement>): boolean {
    if (dragSource) return dragSource.parentId !== ROOT_PARENT_ID
    return hasFolderDragPayload(event.dataTransfer)
  }

  function dropOnRoot(event: DragEvent<HTMLElement>) {
    const ids =
      dragSourceId != null
        ? [dragSourceId]
        : (readFolderDragPayload(event.dataTransfer)?.folderIds ?? [])
    setDragSourceId(null)
    for (const id of ids) {
      const row = rows?.find((candidate) => candidate.id === id)
      if (!row || row.parent_id === ROOT_PARENT_ID) continue
      //  Cùng luật với thả vào một thư mục: nhánh có văn bản phải hỏi lại.
      if (row.document_count_branch > 0) {
        setPendingDrop({ source: row, targetId: ROOT_PARENT_ID })
        continue
      }
      moveFolder.mutate({ id, newParentId: ROOT_PARENT_ID })
    }
  }

  /** Mọi thư mục THẬT (không phải dòng tạm «thư mục mới») đều nhận payload ngoài — quyền thật gác ở backend, lỗi tự toast. */
  function acceptsExternalDrop(node: TreeNode<DocFolderTreeNode>): boolean {
    return Boolean(node.data) && node.id !== NEW_FOLDER_TEMP_ID
  }

  /**
   * Thả văn bản/thư mục kéo từ khung nội dung bên phải vào một nút cây — đúng
   * hợp đồng kéo thả §A/§B (`phase-10-giao-dien-kieu-drive-va-vscode.md`).
   * Văn bản → CHUYỂN sang đích (đổi 24/09/2026: mặc định cũ là THÊM, người
   * dùng thấy văn bản «nhân bản» ra hai chỗ): gắn vào đích rồi gỡ khỏi
   * `sourceFolderId` SAU KHI gắn thành công, không gỡ trước — thất bại giữa
   * chừng thì văn bản không bị treo ngoài mọi thư mục. Giữ Alt/Option lúc thả
   * = THÊM một chỗ nữa (giữ cả thư mục cũ). Thư mục →
   * đổi cha, bỏ qua nếu trùng chính đích (kéo thả nhầm lên chính nó).
   */
  function onExternalDropNode(node: TreeNode<DocFolderTreeNode>, event: DragEvent<HTMLDivElement>) {
    const payload = readFolderDragPayload(event.dataTransfer)
    if (!payload) return
    const targetId = Number(node.id)
    const { documentIds, folderIds, sourceFolderId } = payload

    if (documentIds.length > 0) {
      linkDocuments.mutate(
        { document_ids: documentIds, folder_id: targetId, mode: FOLDER_LINK_MODE.add },
        {
          onSuccess: () => {
            const keepInSource = event.altKey
            if (!keepInSource && sourceFolderId != null && sourceFolderId !== targetId) {
              unlinkDocuments.mutate({ document_ids: documentIds, folder_id: sourceFolderId })
            }
          },
        },
      )
    }

    for (const folderId of folderIds) {
      if (folderId !== targetId) moveFolder.mutate({ id: folderId, newParentId: targetId })
    }
  }

  return {
    canDrag,
    onDragStartNode: (node: TreeNode<DocFolderTreeNode>) => setDragSourceId(Number(node.id)),
    onDragEndNode: () => setDragSourceId(null),
    dropState,
    onDropNode,
    canReorderWith,
    onReorderDrop,
    pendingDrop,
    confirmPendingDrop,
    cancelPendingDrop: () => setPendingDrop(null),
    externalDropMimeType: FOLDER_DRAG_MIME,
    acceptsExternalDrop,
    onExternalDropNode,
    canDropOnRoot,
    dropOnRoot,
  }
}
