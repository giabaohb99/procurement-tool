import { usePermission } from '@/core/authorization/use-permission'
import { Switch } from '@/shared/ui/switch'
import { DocumentFolderFilterSelect, FOLDER_FILTER_ALL } from './document-folder-filter-select'

interface FolderFilterControlProps {
  folderId: number
  onFolderIdChange: (id: number) => void
  includeSubfolders: boolean
  onIncludeSubfoldersChange: (value: boolean) => void
}

/**
 * Ô lọc «Thư mục» + công tắc «Gồm thư mục con» của bộ lọc nâng cao màn Văn bản
 * (`outgoing-documents-tab.tsx`, phase 06) — gộp thành MỘT phần tử để cắm
 * thẳng vào cả hàng lọc khổ rộng (`display:contents`) lẫn `QuickFilterSheet`
 * khổ hẹp, cùng khuôn `typeSelect`/`statusSelect`/`fullTextSwitch` đã có ở đó.
 * Tách riêng tệp để không phình thêm tệp tab vốn đã dài.
 */
export function FolderFilterControl({
  folderId,
  onFolderIdChange,
  includeSubfolders,
  onIncludeSubfoldersChange,
}: FolderFilterControlProps) {
  const { can } = usePermission()
  //  Cả ô chọn lẫn công tắc chỉ có nghĩa khi đọc được cây thư mục — thiếu
  //  `doc_folder.read` thì `DocumentFolderFilterSelect` tự ẩn rồi, ẩn LUÔN cả
  //  khối ở đây để không còn trơ lại một công tắc không gắn với gì (H4).
  if (!can('doc_folder', 'read')) return null

  return (
    <div className="flex shrink-0 flex-wrap items-center gap-2">
      <DocumentFolderFilterSelect folderId={folderId} onFolderIdChange={onFolderIdChange} />
      <label className="flex shrink-0 items-center gap-2 text-sm text-muted-foreground">
        <Switch
          checked={includeSubfolders}
          onCheckedChange={onIncludeSubfoldersChange}
          //  Chưa chọn thư mục nào thì "gồm thư mục con" không có nghĩa gì cả.
          disabled={folderId === FOLDER_FILTER_ALL}
          aria-label="Gồm thư mục con"
        />
        Gồm thư mục con
      </label>
    </div>
  )
}
