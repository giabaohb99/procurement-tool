import type { TreeNode } from '@/shared/tree/tree-types'
import {
  makeDocumentLeafId,
  makeEmptyLeafId,
  makeLoadingLeafId,
  makeMoreLeafId,
} from './folder-tree-document-leaf-id'
import type { FolderDocumentLeavesState } from '../hooks/use-folder-tree-document-leaves'
import type { DocFolderTreeNode } from '../types/document-folder'
import type { DocumentRecord } from '../types/document-record'

export type FolderTreeLeafData =
  | { type: 'document'; document: DocumentRecord; folderId: number }
  | { type: 'empty' }
  | { type: 'loading' }
  | { type: 'more'; folderId: number; remaining: number }

/**
 * Chèn văn bản TRỰC TIẾP của mỗi thư mục ĐANG MỞ làm con SAU CÙNG (sau thư
 * mục con thật — kiểu VS Code Explorer: thư mục trước, tệp sau; yêu cầu
 * 23/09/2026 §4). Thư mục không có gì cả (không thư mục con, không văn bản)
 * hiện MỘT dòng «(trống)» mờ, cùng ý «Chưa có thư mục nào» của `TreeView`.
 *
 * Trả kèm map id-dòng-lá → dữ liệu vì `TreeNode<T>` của cây vẫn giữ nguyên
 * `T = DocFolderTreeNode` (không đổi sang hợp kiểu) — đổi `T` sẽ kéo theo mọi
 * renderer/hook kéo thả/đổi tên/tìm kiếm đang có phải viết lại type guard,
 * không đáng cho một tính năng hiển thị THÊM. Bốn loại dòng lá dùng id CHUỖI
 * riêng (`folder-tree-document-leaf-id.ts`) nên `node.data` của chúng luôn
 * `undefined` — renderer đọc `leaves.get(String(node.id))` TRƯỚC khi rơi về
 * nhánh xử lý thư mục thật.
 */
export function insertFolderDocumentLeaves(
  nodes: TreeNode<DocFolderTreeNode>[],
  expandedIds: ReadonlySet<string | number>,
  leavesByFolderId: ReadonlyMap<number, FolderDocumentLeavesState>,
): { tree: TreeNode<DocFolderTreeNode>[]; leaves: Map<string, FolderTreeLeafData> } {
  const leaves = new Map<string, FolderTreeLeafData>()

  function buildLeafRows(folderId: number, hasRealChildren: boolean): TreeNode<DocFolderTreeNode>[] {
    const state = leavesByFolderId.get(folderId)
    if (!state || state.isLoading) {
      if (hasRealChildren) return [] // thư mục con thật đã hiện sẵn — khỏi thêm dòng "đang tải" gây rối mắt
      const id = makeLoadingLeafId(folderId)
      leaves.set(id, { type: 'loading' })
      return [{ id, label: 'Đang tải…' }]
    }

    const rows: TreeNode<DocFolderTreeNode>[] = []
    for (const document of state.documents) {
      const id = makeDocumentLeafId(folderId, document.id)
      leaves.set(id, { type: 'document', document, folderId })
      rows.push({ id, label: document.title })
    }

    const remaining = state.total - state.documents.length
    if (remaining > 0) {
      const id = makeMoreLeafId(folderId)
      leaves.set(id, { type: 'more', folderId, remaining })
      rows.push({ id, label: `Xem thêm ${remaining} văn bản…` })
    }

    if (!hasRealChildren && state.documents.length === 0) {
      const id = makeEmptyLeafId(folderId)
      leaves.set(id, { type: 'empty' })
      rows.push({ id, label: '(trống)' })
    }
    return rows
  }

  function walk(list: TreeNode<DocFolderTreeNode>[]): TreeNode<DocFolderTreeNode>[] {
    return list.map((node) => {
      const realChildren = node.children?.length ? walk(node.children) : []
      const folderId = typeof node.id === 'number' ? node.id : null
      if (folderId == null || !expandedIds.has(folderId)) {
        return realChildren.length ? { ...node, children: realChildren } : node
      }
      const leafRows = buildLeafRows(folderId, realChildren.length > 0)
      if (realChildren.length === 0 && leafRows.length === 0) return node
      return { ...node, children: [...realChildren, ...leafRows] }
    })
  }

  return { tree: walk(nodes), leaves }
}
