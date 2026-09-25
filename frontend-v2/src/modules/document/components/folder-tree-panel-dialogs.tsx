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
import { buttonVariants } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'
import { FolderMoveDialog } from './folder-move-dialog'
import type { useFolderDragMove } from '../hooks/use-folder-drag-move'
import type { useFolderTreeActions } from '../hooks/use-folder-tree-actions'
import { ROOT_PARENT_ID } from '../helpers/insert-temp-tree-node'
import { FOLDER_KIND } from '../types/document-folder'
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
  const { moveTarget, setMoveTarget, deleteTarget, setDeleteTarget, deleteFolder } = actions
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

      <AlertDialog
        open={deleteTarget != null}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            {deleteTarget?.kind === FOLDER_KIND.company ? (
              <>
                <AlertDialogTitle className="break-words">
                  Xóa thư mục pháp nhân "{deleteTarget?.name}"?
                </AlertDialogTitle>
                <AlertDialogDescription>
                  Chỉ xóa được khi RỖNG (không còn thư mục con, không còn văn bản). Văn bản mới
                  không gắn thư mục sẽ tự tạo lại thư mục pháp nhân này khi cần. Thao tác này không
                  hoàn tác được.
                </AlertDialogDescription>
              </>
            ) : (
              <>
                <AlertDialogTitle className="break-words">
                  Xóa thư mục "{deleteTarget?.name}"?
                </AlertDialogTitle>
                <AlertDialogDescription>
                  Chỉ xóa được thư mục RỖNG (không còn thư mục con, không còn văn bản). Thao tác này
                  không hoàn tác được.
                </AlertDialogDescription>
              </>
            )}
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Hủy</AlertDialogCancel>
            <AlertDialogAction
              className={cn(buttonVariants({ variant: 'destructive' }))}
              onClick={() => {
                if (deleteTarget) deleteFolder.mutate(deleteTarget.id)
                setDeleteTarget(null)
              }}
            >
              Xóa
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

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
