import { FileText, Folder, Info, Loader2, TriangleAlert } from 'lucide-react'
import { useRef, useState } from 'react'

import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Label } from '@/shared/ui/label'
import { useDeleteDocFolder, useDocFolderTree, useFolderDeletePreview } from '../hooks/use-document-folders'
import { FOLDER_ACCESS_LEVEL, type DocFolderTreeNode } from '../types/document-folder'
import { FolderPicker } from './folder-picker'

interface FolderDeleteDialogProps {
  folder: DocFolderTreeNode
  onClose: () => void
}

/**
 * HỘP XÓA THƯ MỤC — dùng chung cho menu cây bên trái và menu ⋯ của thư mục con.
 *
 * Xóa được cả khi thư mục CÒN văn bản (đại ca chốt 25/09/2026). Văn bản không
 * bị xóa theo: văn bản còn nằm ở thư mục khác chỉ bị gỡ khỏi thư mục này, còn
 * văn bản CHỈ nằm ở đây sẽ mồ côi — nên hộp BẮT chọn nơi lưu mới cho chúng
 * (gợi ý sẵn thư mục cha) trước khi cho bấm «Xóa». Số đếm là TOÀN HỆ, gồm cả
 * văn bản người xóa không xem được.
 */
export function FolderDeleteDialog({ folder, onClose }: FolderDeleteDialogProps) {
  const preview = useFolderDeletePreview(folder.id)
  const { data: allFolders = [] } = useDocFolderTree(false)
  const deleteFolder = useDeleteDocFolder()
  const [pickedTarget, setPickedTarget] = useState<number | null>(null)
  //  Chặn bấm đúp (bẫy CR-317) — `isPending` chỉ đúng từ lượt render sau.
  const deletingRef = useRef(false)

  const info = preview.data
  const name = folder.display_name ?? folder.name
  //  Gợi ý thư mục cha, nhưng chỉ khi mình thêm được văn bản vào đó (mức Đóng
  //  góp trở lên) — gợi ý một chỗ không được phép thì bấm Xóa là ăn 403.
  const parent = allFolders.find((item) => item.id === info?.parent_id)
  const suggested =
    parent && parent.my_level >= FOLDER_ACCESS_LEVEL.contribute ? parent.id : null
  const target = pickedTarget ?? suggested
  const orphanCount = info?.orphan_count ?? 0
  const sharedCount = (info?.document_count ?? 0) - orphanCount
  const pickedSelf = target === folder.id
  const canDelete =
    Boolean(info) && !info?.blocked_reason && (orphanCount === 0 || (target != null && !pickedSelf))

  function handleDelete() {
    if (!canDelete || deletingRef.current) return
    deletingRef.current = true
    deleteFolder.mutate(
      { id: folder.id, moveTo: orphanCount > 0 && target ? target : undefined },
      {
        onSuccess: onClose,
        onSettled: () => {
          deletingRef.current = false
        },
      },
    )
  }

  return (
    <Dialog open onOpenChange={(open) => !open && !deleteFolder.isPending && onClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Xóa thư mục</DialogTitle>
          {/*  Tên thư mục đứng riêng một dòng kèm icon — không kẹp «» vào tiêu đề
               (đại ca chê 25/09/2026, cùng khuôn hộp Chia sẻ). */}
          <DialogDescription className="flex min-w-0 items-center gap-1.5 pr-6 font-medium text-foreground">
            <Folder className="size-4 shrink-0 text-muted-foreground" />
            <span className="truncate" title={name}>
              {name}
            </span>
          </DialogDescription>
        </DialogHeader>

        {preview.isLoading || !info ? (
          <p className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Đang đếm văn bản trong thư mục…
          </p>
        ) : info.blocked_reason ? (
          <p className="flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
            <TriangleAlert className="mt-0.5 size-4 shrink-0" />
            {info.blocked_reason}
          </p>
        ) : (
          <div className="space-y-4 text-sm">
            <div className="flex items-start gap-3 rounded-md border px-3 py-2.5">
              <FileText className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
              {info.document_count === 0 ? (
                <p>Thư mục đang trống.</p>
              ) : (
                <div className="space-y-0.5">
                  <p>
                    <span className="font-medium">{info.document_count} văn bản</span> trong thư mục
                    — văn bản không bị xóa theo.
                  </p>
                  {sharedCount > 0 && (
                    <p className="text-muted-foreground">
                      {sharedCount} văn bản còn nằm ở thư mục khác, chỉ gỡ khỏi thư mục này.
                    </p>
                  )}
                </div>
              )}
            </div>

            {orphanCount > 0 && (
              <div className="space-y-1.5">
                <Label className="gap-0">
                  Chuyển văn bản sang
                  <span className="text-destructive">*</span>
                </Label>
                <FolderPicker
                  folderIds={target ? [target] : []}
                  primaryFolderId={target}
                  onChange={(ids) => ids[0] && setPickedTarget(ids[0])}
                  multiple={false}
                  hideChips
                  placeholder="Chọn nơi lưu mới cho văn bản…"
                />
                {pickedSelf ? (
                  <p className="text-xs text-destructive">
                    Không chuyển vào chính thư mục đang xóa — chọn thư mục khác.
                  </p>
                ) : (
                  <p className="text-xs text-muted-foreground">
                    {orphanCount} văn bản chỉ nằm trong thư mục này sẽ chuyển sang đây.
                  </p>
                )}
              </div>
            )}

            <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Info className="size-3.5 shrink-0" />
              Xóa thư mục không hoàn tác được.
            </p>
          </div>
        )}

        <DialogFooter>
          <Button type="button" variant="ghost" disabled={deleteFolder.isPending} onClick={onClose}>
            Hủy
          </Button>
          <Button
            type="button"
            variant="destructive"
            disabled={!canDelete || deleteFolder.isPending}
            onClick={handleDelete}
          >
            {deleteFolder.isPending && <Loader2 className="size-4 animate-spin" />}
            {orphanCount > 0 ? 'Chuyển văn bản và xóa' : 'Xóa'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
