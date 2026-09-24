import { FolderInput, FolderPlus, FolderX, X } from 'lucide-react'
import { useState } from 'react'

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Button } from '@/shared/ui/button'
import { folderBulkResultMessage } from '../helpers/folder-bulk-result-message'
import { useLinkDocumentsToFolder, useUnlinkDocumentsFromFolder } from '../hooks/use-document-folders'
import { FOLDER_LINK_MODE } from '../types/document-folder'
import { FolderPicker } from './folder-picker'

interface FolderBulkActionsProps {
  selectedIds: number[]
  /**
   * Thư mục ĐANG XEM — chỉ có ở trang Quản lý cây thư mục. Có giá trị thì
   * hiện thêm nút «Chuyển tới…» + «Gỡ khỏi thư mục này» (gỡ đúng khỏi đây,
   * không hỏi lại); bỏ trống thì CHỈ hiện «Thêm vào thư mục…» — dùng ở màn
   * Văn bản (`outgoing-documents-tab.tsx`, phase 06), nơi không có khái niệm
   * "thư mục đang xem" (một dòng có thể không nằm trong thư mục nào đang lọc).
   */
  currentFolder?: { id: number; name: string }
  onClearSelection: () => void
}

type PickerMode = 'add' | 'move' | null

/**
 * Thanh thao tác HÀNG LOẠT hiện khi một bảng văn bản có dòng đang tick — dùng
 * chung cho khung nội dung thư mục (`folder-documents-table.tsx`, đủ ba nút)
 * VÀ màn Văn bản (`outgoing-documents-tab.tsx`, chỉ nút «Thêm vào thư mục…» vì
 * không có "thư mục đang xem" để chuyển-tới/gỡ-khỏi).
 *
 * ⚠️ Gửi lên backend đúng DANH SÁCH ID client đang có trên bảng — không có
 * khái niệm "chọn tất cả trong thư mục" chạy phía server, vì người xem có thể
 * chỉ thấy MỘT PHẦN văn bản trong thư mục (bảng "Thấy một phần", phase 04) và
 * "chọn tất cả" kiểu server sẽ động tới cả phần họ không thấy.
 */
export function FolderBulkActions({ selectedIds, currentFolder, onClearSelection }: FolderBulkActionsProps) {
  const [pickerMode, setPickerMode] = useState<PickerMode>(null)
  const [resultMessage, setResultMessage] = useState<string | null>(null)
  const link = useLinkDocumentsToFolder()
  const unlink = useUnlinkDocumentsFromFolder()

  function runUnlink() {
    if (!currentFolder) return
    unlink.mutate(
      { document_ids: selectedIds, folder_id: currentFolder.id },
      {
        onSuccess: (result) => {
          setResultMessage(folderBulkResultMessage('gỡ', result))
          onClearSelection()
        },
      },
    )
  }

  if (selectedIds.length === 0 && !resultMessage) return null

  return (
    <div className="flex flex-wrap items-center gap-2 rounded-md border bg-muted/40 px-3 py-2 text-sm">
      {selectedIds.length > 0 && (
        <>
          <span className="font-medium tabular-nums">Đã chọn {selectedIds.length} văn bản</span>
          <Button type="button" variant="outline" size="sm" onClick={() => setPickerMode('add')}>
            <FolderPlus className="size-4" />
            Thêm vào thư mục…
          </Button>
          {currentFolder && (
            <>
              <Button type="button" variant="outline" size="sm" onClick={() => setPickerMode('move')}>
                <FolderInput className="size-4" />
                Chuyển tới…
              </Button>
              <Button type="button" variant="outline" size="sm" onClick={runUnlink} disabled={unlink.isPending}>
                <FolderX className="size-4" />
                Gỡ khỏi «{currentFolder.name}»
              </Button>
            </>
          )}
          <Button type="button" variant="ghost" size="sm" onClick={onClearSelection}>
            Bỏ chọn
          </Button>
        </>
      )}

      {resultMessage && (
        <span className="flex items-center gap-2 text-muted-foreground">
          {resultMessage}
          <button
            type="button"
            aria-label="Đóng thông báo kết quả"
            onClick={() => setResultMessage(null)}
            className="rounded p-0.5 hover:bg-muted"
          >
            <X className="size-3.5" />
          </button>
        </span>
      )}

      <Dialog open={pickerMode != null} onOpenChange={(open) => !open && setPickerMode(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>
              {pickerMode === 'move' ? 'Chuyển tới thư mục…' : 'Thêm vào thư mục…'}
            </DialogTitle>
            <DialogDescription>
              {pickerMode === 'move'
                ? `Thay thư mục hiện tại của ${selectedIds.length} văn bản đã chọn bằng thư mục dưới đây.`
                : `Gắn thêm ${selectedIds.length} văn bản đã chọn vào thư mục dưới đây, giữ nguyên các thư mục khác.`}
            </DialogDescription>
          </DialogHeader>

          <FolderPicker
            folderIds={[]}
            primaryFolderId={null}
            multiple={false}
            onChange={(ids) => {
              const folderId = ids[0]
              if (!folderId) return
              link.mutate(
                {
                  document_ids: selectedIds,
                  folder_id: folderId,
                  mode: pickerMode === 'move' ? FOLDER_LINK_MODE.replace : FOLDER_LINK_MODE.add,
                },
                {
                  onSuccess: (result) => {
                    setResultMessage(folderBulkResultMessage(pickerMode === 'move' ? 'chuyển' : 'thêm', result))
                    onClearSelection()
                  },
                },
              )
              setPickerMode(null)
            }}
          />

          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => setPickerMode(null)}>
              Hủy
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
