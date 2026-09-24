import { FolderInput, FolderPlus, FolderX, Info, TriangleAlert, Trash2, X } from 'lucide-react'
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
import { IconTooltip } from '@/shared/ui/icon-tooltip'
import {
  MAX_BULK_DOCUMENT_IDS,
  MAX_BULK_FOLDER_IDS,
  useFolderSelectionBulkActions,
} from '../hooks/use-folder-selection-bulk-actions'
import { FolderPicker } from './folder-picker'

export { MAX_BULK_DOCUMENT_IDS, MAX_BULK_FOLDER_IDS }

type PickerMode = 'add' | 'move' | null

interface FolderSelectionToolbarProps {
  selectedFolderIds: number[]
  selectedDocumentIds: number[]
  currentFolder: { id: number; name: string }
  onClearSelection: () => void
  onShowDetails: () => void
}

/**
 * THANH THAO TÁC kiểu Drive (đặc tả §B, phản hồi 24/09/2026) — thay NGUYÊN
 * hàng tìm/lọc khi có lượt chọn (`folder-documents-view.tsx` swap ở CÙNG một
 * chỗ, không xếp chồng lên nhau như bản cũ): «✕» + «n mục đã chọn» + các nút
 * CHỈ ICON có tooltip (Thêm vào thư mục · Chuyển tới · Gỡ khỏi thư mục này ·
 * Xóa (tô màu nguy hiểm) · Chi tiết) — không còn nhãn chữ dài kiểu form cũ.
 *
 * Khác `folder-bulk-actions.tsx` (giữ nguyên cho `outgoing-documents-tab.tsx`,
 * chỉ biết văn bản): thanh này biết cả THƯ MỤC lẫn văn bản trong CÙNG một
 * lượt chọn (khung nội dung kiểu Drive chọn được cả hai loại thẻ).
 *
 * «Thêm vào thư mục…» chỉ có nghĩa với văn bản (một thư mục chỉ có MỘT cha,
 * không "thêm" được) — ẩn hẳn khi có thư mục trong lượt chọn thay vì hiện rồi
 * âm thầm bỏ qua phần thư mục.
 *
 * Mutation/trần/phím `Delete` nằm ở `use-folder-selection-bulk-actions.ts` —
 * tệp này chỉ còn lo GIAO DIỆN.
 */
export function FolderSelectionToolbar({
  selectedFolderIds,
  selectedDocumentIds,
  currentFolder,
  onClearSelection,
  onShowDetails,
}: FolderSelectionToolbarProps) {
  const [pickerMode, setPickerMode] = useState<PickerMode>(null)
  const bulk = useFolderSelectionBulkActions({
    selectedFolderIds,
    selectedDocumentIds,
    currentFolder,
    onClearSelection,
  })

  if (bulk.total === 0) return null

  return (
    <div className="flex h-9 items-center gap-1 rounded-md border bg-muted/40 px-1.5 text-sm">
      <IconTooltip label="Bỏ chọn">
        <Button type="button" variant="ghost" size="icon-sm" aria-label="Bỏ chọn" onClick={onClearSelection}>
          <X className="size-4" />
        </Button>
      </IconTooltip>

      <span className="px-1 font-medium tabular-nums">{bulk.total} mục đã chọn</span>

      {bulk.overCap && (
        <IconTooltip
          label={
            [
              bulk.overDocCap && `Chỉ thao tác được tối đa ${MAX_BULK_DOCUMENT_IDS} văn bản một lượt.`,
              bulk.overFolderCap && `Chỉ chuyển được tối đa ${MAX_BULK_FOLDER_IDS} thư mục một lượt.`,
            ]
              .filter(Boolean)
              .join(' ')
          }
        >
          <TriangleAlert className="size-4 shrink-0 text-destructive" aria-label="Vượt trần thao tác hàng loạt" />
        </IconTooltip>
      )}

      <div className="ml-auto flex items-center gap-0.5">
        {!bulk.hasFolders && (
          <IconTooltip label="Thêm vào thư mục">
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              aria-label="Thêm vào thư mục"
              disabled={bulk.overCap}
              onClick={() => setPickerMode('add')}
            >
              <FolderPlus className="size-4" />
            </Button>
          </IconTooltip>
        )}
        <IconTooltip label="Chuyển tới">
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            aria-label="Chuyển tới"
            disabled={bulk.overCap}
            onClick={() => setPickerMode('move')}
          >
            <FolderInput className="size-4" />
          </Button>
        </IconTooltip>
        {!bulk.hasFolders && (
          <IconTooltip label={`Gỡ khỏi «${currentFolder.name}»`}>
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              aria-label={`Gỡ khỏi «${currentFolder.name}»`}
              disabled={bulk.overCap}
              onClick={bulk.runUnlink}
            >
              <FolderX className="size-4" />
            </Button>
          </IconTooltip>
        )}
        {bulk.showDelete && (
          <IconTooltip label="Xóa">
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              aria-label="Xóa"
              disabled={bulk.overCap}
              className="text-destructive hover:bg-destructive/10 hover:text-destructive"
              onClick={() => void bulk.runDelete()}
            >
              <Trash2 className="size-4" />
            </Button>
          </IconTooltip>
        )}
        <IconTooltip label="Chi tiết">
          <Button type="button" variant="ghost" size="icon-sm" aria-label="Chi tiết" onClick={onShowDetails}>
            <Info className="size-4" />
          </Button>
        </IconTooltip>
      </div>

      <Dialog open={pickerMode != null} onOpenChange={(open) => !open && setPickerMode(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{pickerMode === 'move' ? 'Chuyển tới thư mục…' : 'Thêm vào thư mục…'}</DialogTitle>
            <DialogDescription>
              {pickerMode === 'move'
                ? `Đổi cha của ${bulk.total} mục đã chọn thành thư mục dưới đây.`
                : `Gắn thêm ${selectedDocumentIds.length} văn bản đã chọn vào thư mục dưới đây, giữ nguyên các thư mục khác.`}
            </DialogDescription>
          </DialogHeader>

          <FolderPicker
            folderIds={[]}
            primaryFolderId={null}
            multiple={false}
            onChange={(ids) => {
              const targetId = ids[0]
              if (!targetId) return
              const mode = pickerMode
              setPickerMode(null)
              if (mode === 'move') bulk.runMoveTo(targetId)
              else bulk.runAdd(targetId)
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
