import { DocumentFolderFilterSelect } from './document-folder-filter-select'

interface FolderFilterControlProps {
  folderId: number
  onFolderIdChange: (id: number) => void
  includeSubfolders: boolean
  onIncludeSubfoldersChange: (value: boolean) => void
}

/**
 * Ô lọc «Thư mục» của màn Văn bản (`outgoing-documents-tab.tsx`, phase 06) —
 * dùng chung cho hàng lọc khổ rộng lẫn `QuickFilterSheet` khổ hẹp.
 *
 * «Gồm thư mục con» nay nằm Ở CHÂN popover của ô chọn (25/09/2026) thay vì
 * một công tắc đứng riêng ngoài thanh: nó chỉ có nghĩa khi đã chọn thư mục,
 * và đứng ngoài thì trông như một bộ lọc độc lập đang bật. Thiếu
 * `doc_folder.read` thì ô chọn tự ẩn (H4).
 */
export function FolderFilterControl({
  folderId,
  onFolderIdChange,
  includeSubfolders,
  onIncludeSubfoldersChange,
}: FolderFilterControlProps) {
  return (
    <DocumentFolderFilterSelect
      folderId={folderId}
      onFolderIdChange={onFolderIdChange}
      includeSubfolders={includeSubfolders}
      onIncludeSubfoldersChange={onIncludeSubfoldersChange}
    />
  )
}
