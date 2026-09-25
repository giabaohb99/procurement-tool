import { FolderDeleteDialog } from './folder-delete-dialog'
import { FolderMoveDialog } from './folder-move-dialog'
import { FolderRenameDialog } from './folder-rename-dialog'
import { FolderShareDialog } from './folder-share-dialog'
import { useDocFolderTree } from '../hooks/use-document-folders'
import type { useFolderRowActions } from '../hooks/use-folder-row-actions'

interface FolderRowActionDialogsProps {
  actions: ReturnType<typeof useFolderRowActions>
  /** Hộp «Chia sẻ» điều hướng được sang thư mục khác (bấm vào một dòng kế thừa) — nơi gọi tự quyết định mở thư mục đó ở đâu. */
  onNavigateToFolder: (id: number) => void
}

/**
 * Bốn hộp thoại DÙNG CHUNG của một dòng thư mục con (đổi tên · chuyển tới… ·
 * chia sẻ · xóa) — đi kèm `useFolderRowActions`, dựng MỘT LẦN ở cấp cha
 * (`folder-child-cards.tsx`/`folder-list-view.tsx`) thay vì mỗi dòng tự mở
 * hộp thoại của riêng nó.
 */
export function FolderRowActionDialogs({ actions, onNavigateToFolder }: FolderRowActionDialogsProps) {
  //  Chỉ nạp toàn cây khi thật sự cần (mở hộp «Chuyển tới…») — tránh gọi API thừa lúc chỉ hiện dòng/thẻ.
  const { data: allFolders } = useDocFolderTree(false, actions.moveTarget != null)

  return (
    <>
      {actions.renameTarget && (
        <FolderRenameDialog
          folderId={actions.renameTarget.id}
          currentName={actions.renameTarget.name}
          open
          onOpenChange={(open) => !open && actions.setRenameTarget(null)}
        />
      )}

      {actions.moveTarget && allFolders && (
        <FolderMoveDialog
          folder={actions.moveTarget}
          rows={allFolders}
          open
          onOpenChange={(open) => !open && actions.setMoveTarget(null)}
        />
      )}

      {actions.deleteTarget && (
        <FolderDeleteDialog folder={actions.deleteTarget} onClose={() => actions.setDeleteTarget(null)} />
      )}

      {actions.shareTargetId != null && (
        <FolderShareDialog
          folderId={actions.shareTargetId}
          open
          onOpenChange={(open) => !open && actions.setShareTargetId(null)}
          onNavigateToFolder={(id) => {
            actions.setShareTargetId(null)
            onNavigateToFolder(id)
          }}
        />
      )}
    </>
  )
}
