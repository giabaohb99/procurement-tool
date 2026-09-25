import { Folder as FolderIcon, Plus } from 'lucide-react'

import type { TreeNode } from '@/shared/tree/tree-types'
import type { useTreeExpansion } from '@/shared/tree/use-tree-expansion'
import { buildFolderTooltip } from '../helpers/folder-tree-tooltip'
import type { FolderTreeLeafData } from '../helpers/insert-folder-document-leaves'
import { NEW_FOLDER_TEMP_ID } from '../helpers/insert-temp-tree-node'
import type { useFolderTreeActions } from '../hooks/use-folder-tree-actions'
import { FOLDER_ACCESS_LEVEL } from '../types/document-folder'
import type { DocFolderTreeNode } from '../types/document-folder'
import { FolderTreeActionsMenu } from './folder-tree-actions-menu'
import { FolderTreeLeafIcon, FolderTreeLeafLabel } from './folder-tree-document-leaf-item'
import { FolderCountBadge, FolderNodeIcon, FolderNodeLabel, FolderRenameInput } from './folder-tree-item'

interface BuildRowRenderersOptions {
  expansion: ReturnType<typeof useTreeExpansion>
  actions: ReturnType<typeof useFolderTreeActions>
  keyword: string
  beginCreate: (node: DocFolderTreeNode) => void
  /** Vai trò có `doc_folder.create` — thiếu thì ẩn nút "+" thêm thư mục con. */
  canCreateFolder: boolean
  onSelectFolder: (id: number) => void
  onOpenAccessTab: (id: number) => void
  /** Dòng LÁ chèn thêm (văn bản/trống/đang tải/xem thêm) — `undefined` với dòng thư mục thật. Xem `insert-folder-document-leaves.ts`. */
  leaves: ReadonlyMap<string, FolderTreeLeafData>
  /** Mọi thư mục NGƯỜI DÙNG NÀY thấy được, theo id — dựng tooltip full path (`folder-tree-tooltip.ts`). */
  rowsById: ReadonlyMap<number, DocFolderTreeNode>
}

/**
 * Tạo được thư mục con trong `node` — ngưỡng dùng cho nút "+" thêm con VÀ nút
 * "Thư mục mới". Cần CẢ HAI lớp như backend (`require('doc_folder','create')`
 * rồi `ensure_level(CONTRIBUTE)`): mức Đóng góp giờ có thể đến từ quyền GHI
 * văn bản (`role_level_cap`), mà người đó chưa chắc được tạo thư mục.
 */
export function canManageNode(node: DocFolderTreeNode, canCreateFolder: boolean): boolean {
  return canCreateFolder && node.my_level >= FOLDER_ACCESS_LEVEL.contribute
}

/**
 * Năm hàm `render*` truyền vào `TreeView` của cây thư mục — gom vào một hàm
 * riêng để `folder-tree-panel.tsx` giữ dưới 200 dòng. Hàm THUẦN (không tự gọi
 * hook nào), chỉ đóng gói state/hành động đã có sẵn từ nơi gọi thành JSX.
 */
export function buildFolderTreeRowRenderers({
  expansion,
  actions,
  keyword,
  beginCreate,
  canCreateFolder,
  onSelectFolder,
  onOpenAccessTab,
  leaves,
  rowsById,
}: BuildRowRenderersOptions) {
  return {
    renderIcon: (node: TreeNode<DocFolderTreeNode>) => {
      if (node.id === NEW_FOLDER_TEMP_ID) {
        return <FolderIcon className="size-4 shrink-0 text-foreground" />
      }
      const leaf = leaves.get(String(node.id))
      if (leaf) return <FolderTreeLeafIcon leaf={leaf} />
      return <FolderNodeIcon data={node.data} expanded={expansion.isExpanded(node.id)} />
    },

    renderBadge: (node: TreeNode<DocFolderTreeNode>) =>
      node.id === NEW_FOLDER_TEMP_ID || leaves.has(String(node.id)) ? null : (
        <FolderCountBadge data={node.data} />
      ),

    renderLabel: (node: TreeNode<DocFolderTreeNode>) => {
      if (node.id === NEW_FOLDER_TEMP_ID) {
        return (
          <FolderRenameInput
            value={actions.newFolderValue}
            onChange={actions.setNewFolderValue}
            onCommit={() => actions.commitCreate((folder) => onSelectFolder(folder.id))}
            onCancel={actions.cancelCreate}
            label="Tên thư mục mới"
            placeholder="Tên thư mục mới…"
          />
        )
      }
      const leaf = leaves.get(String(node.id))
      if (leaf) return <FolderTreeLeafLabel leaf={leaf} label={node.label} />
      if (node.data && actions.renamingId === node.data.id) {
        return (
          <FolderRenameInput
            value={actions.renameValue}
            onChange={actions.setRenameValue}
            onCommit={() => actions.commitRename(node.data?.name)}
            onCancel={actions.cancelRename}
            label={`Đổi tên ${node.label}`}
          />
        )
      }
      return <FolderNodeLabel label={node.label} keyword={keyword} />
    },

    renderHoverActions: (node: TreeNode<DocFolderTreeNode>) =>
      node.data && canManageNode(node.data, canCreateFolder) ? (
        <button
          type="button"
          aria-label={`Thêm thư mục con vào ${node.data.name}`}
          onClick={(event) => {
            event.stopPropagation()
            beginCreate(node.data as DocFolderTreeNode)
          }}
          className="flex size-5 shrink-0 items-center justify-center rounded hover:bg-muted"
        >
          <Plus className="size-3.5" />
        </button>
      ) : null,

    renderTrailing: (node: TreeNode<DocFolderTreeNode>) =>
      node.data ? (
        <FolderTreeActionsMenu
          data={node.data}
          onAction={(action) => {
            if (action === 'add-child') beginCreate(node.data as DocFolderTreeNode)
            else actions.handleAction(node.data as DocFolderTreeNode, action, onOpenAccessTab)
          }}
        />
      ) : null,

    /** Số hiệu văn bản (lá) hoặc tên pháp lý đầy đủ + đường dẫn (thư mục) — yêu cầu §2, 23/09/2026. */
    getTooltip: (node: TreeNode<DocFolderTreeNode>): string | undefined => {
      if (node.id === NEW_FOLDER_TEMP_ID) return undefined
      const leaf = leaves.get(String(node.id))
      if (leaf) return leaf.type === 'document' ? leaf.document.display_code || undefined : undefined
      return node.data ? buildFolderTooltip(node.data, rowsById) : undefined
    },
  }
}
