import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/shared/ui/alert-dialog'
import { FolderDeleteDialog } from './folder-delete-dialog'
import { FolderMoveDialog } from './folder-move-dialog'
import type { useFolderDragMove } from '../hooks/use-folder-drag-move'
import type { useFolderTreeActions } from '../hooks/use-folder-tree-actions'
import { ROOT_PARENT_ID } from '../helpers/insert-temp-tree-node'
import type { DocFolderTreeNode } from '../types/document-folder'

interface FolderTreePanelDialogsProps {
  actions: ReturnType<typeof useFolderTreeActions>
  drag: ReturnType<typeof useFolderDragMove>
  rows: DocFolderTreeNode[] | undefined
}

/**
 * Ba hộp thoại còn lại của khung cây (chuyển tới · xóa · xác nhận kéo thả
 * nhánh có văn bản) gom vào một tệp riêng, để `folder-tree-panel.tsx` chỉ còn
 * phần cây + thanh công cụ.
 *
 * ⚠️ «Thêm thư mục con» KHÔNG còn là hộp thoại (duoc-CR-476, 23/09/2026) — dòng
 * nhập tạm hiện NGAY trong cây (`insertTempChildNode`), nên không cần `onExpand`/
 * `onSelectFolder` ở đây nữa.
 */
export function FolderTreePanelDialogs({ actions, drag, rows }: FolderTreePanelDialogsProps) {
  const { moveTarget, setMoveTarget, deleteTarget, setDeleteTarget } = actions
  const { pendingDrop, confirmPendingDrop, cancelPendingDrop } = drag

  return (
    <>
      {moveTarget && rows && (
        <FolderMoveDialog
          open
          onOpenChange={(open) => !open && setMoveTarget(null)}
          folder={moveTarget}
          rows={rows}
        />
      )}

      {/*  Xóa được cả thư mục còn văn bản — hộp tự đếm và bắt chọn nơi lưu mới
           cho văn bản sẽ mồ côi (25/09/2026). */}
      {deleteTarget && (
        <FolderDeleteDialog folder={deleteTarget} onClose={() => setDeleteTarget(null)} />
      )}

      <AlertDialog open={pendingDrop != null} onOpenChange={(open) => !open && cancelPendingDrop()}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="break-words">
              {pendingDrop?.targetId === ROOT_PARENT_ID
                ? `Chuyển «${pendingDrop?.source.name}» ra gốc cây?`
                : `Chuyển «${pendingDrop?.source.name}» tới thư mục này?`}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {pendingDrop?.source.document_count_branch} văn bản bạn xem được, và có thể còn văn
              bản bạn không xem được sẽ đi theo nhánh này.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Hủy</AlertDialogCancel>
            <AlertDialogAction onClick={confirmPendingDrop}>Chuyển tới đây</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
