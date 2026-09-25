import { useState } from 'react'

import { cn } from '@/shared/utils/cn'
import type { FolderDragPayload } from '../helpers/folder-drag-payload'
import { folderItemKey } from '../helpers/folder-item-id'
import {
  DOCUMENT_SORT_FIELD,
  type DocumentSortField,
  type SortDirection,
} from '../helpers/sort-document-rows'
import { useFolderRowActions } from '../hooks/use-folder-row-actions'
import type { useFolderContentSelection } from '../hooks/use-folder-content-selection'
import type { DocFolderTreeNode } from '../types/document-folder'
import type { DocumentRecord } from '../types/document-record'
import { FolderItemSelectCheckbox } from './folder-item-select-checkbox'
import {
  FOLDER_LIST_GRID_TEMPLATE,
  FOLDER_LIST_GRID_TEMPLATE_NO_SELECT,
  FOLDER_LIST_OWNER_COLUMN,
  FolderListRow,
} from './folder-list-row'
import { FolderRowActionDialogs } from './folder-row-action-dialogs'
import { FolderSortButton } from './folder-sort-button'

interface FolderListViewProps {
  children: DocFolderTreeNode[]
  documents: DocumentRecord[]
  /** `null` = không gắn với một thư mục cụ thể (gốc «Thư mục của bạn»). */
  sourceFolderId: number | null
  isFullText: boolean
  sortField: DocumentSortField
  sortDir: SortDirection
  onSortFieldChange: (field: DocumentSortField) => void
  onToggleSortDir: () => void
  selection: ReturnType<typeof useFolderContentSelection>
  onOpenFolder: (id: number) => void
  onOpenDocument: (document: DocumentRecord) => void
  onViewFolderDetails: (folder: DocFolderTreeNode) => void
  onViewDocumentDetails: (document: DocumentRecord) => void
  onDropOnFolder: (targetFolderId: number, payload: FolderDragPayload, keepInSource: boolean) => void
  onMoveDocumentTo: (document: DocumentRecord) => void
  /** «Chia sẻ…» của một dòng VĂN BẢN — mở hộp quyền truy cập của văn bản đó. Bỏ trống ở gốc «Thư mục của bạn» (không có dòng văn bản). */
  onShareDocument?: (document: DocumentRecord) => void
  onRemoveDocument: (document: DocumentRecord) => void
  canWrite: boolean
  canDelete: boolean
  /** `false` = bỏ cột ô tick (cả «Chọn tất cả») — gốc «Thư mục của bạn». Mặc định `true`. */
  selectable?: boolean
}

/**
 * DANH SÁCH kiểu Drive (đặc tả §1/§B, duoc-CR-476 + phản hồi 24/09/2026) —
 * MỘT bảng duy nhất thay `DataTable`: tiêu đề dính (`sticky top-0`), THƯ MỤC
 * trước rồi VĂN BẢN (không phải hai khối tách rời như chế độ Lưới), không cột
 * tick riêng (ô tick nổi trong ô Tên, xem `folder-list-row.tsx`), không cuộn
 * ngang (5 cột cố định + 1 co giãn).
 *
 * Tự giữ `useFolderRowActions` + `FolderRowActionDialogs` (đổi tên/chuyển
 * tới/chia sẻ/xóa THƯ MỤC) — cùng khuôn tự-chứa với `folder-child-cards.tsx`
 * (chế độ Lưới), để `folder-documents-view.tsx` không phải tãi thêm một lô
 * callback rời rạc.
 */
export function FolderListView({
  children,
  documents,
  sourceFolderId,
  isFullText,
  sortField,
  sortDir,
  onSortFieldChange,
  onToggleSortDir,
  selection,
  onOpenFolder,
  onOpenDocument,
  onViewFolderDetails,
  onViewDocumentDetails,
  onDropOnFolder,
  onMoveDocumentTo,
  onShareDocument,
  onRemoveDocument,
  canWrite,
  canDelete,
  selectable = true,
}: FolderListViewProps) {
  const rowActions = useFolderRowActions()
  const [dragOverFolderId, setDragOverFolderId] = useState<number | null>(null)

  if (children.length === 0 && documents.length === 0) return null

  const itemKeys = [
    ...children.map((folder) => folderItemKey('folder', folder.id)),
    ...documents.map((document) => folderItemKey('document', document.id)),
  ]
  const selectedCount = itemKeys.filter((key) => selection.isSelected(key)).length
  const allSelected = selectedCount === itemKeys.length
  const someSelected = selectedCount > 0

  return (
    <div className="@container overflow-hidden rounded-md border">
      <div
        className={cn(
          selectable ? FOLDER_LIST_GRID_TEMPLATE : FOLDER_LIST_GRID_TEMPLATE_NO_SELECT,
          'sticky top-0 z-10 h-9 items-center border-b bg-muted/40 px-3 text-xs font-medium text-muted-foreground',
        )}
        role="row"
      >
        {selectable && (
          <FolderItemSelectCheckbox
            checked={allSelected ? true : someSelected ? 'indeterminate' : false}
            onToggle={() => (allSelected ? selection.clear() : selection.selectAll())}
            label="Chọn tất cả"
          />
        )}
        <FolderSortButton
          label="Tên"
          field={DOCUMENT_SORT_FIELD.name}
          activeField={sortField}
          dir={sortDir}
          onSortFieldChange={onSortFieldChange}
          onToggleSortDir={onToggleSortDir}
        />
        <span className={FOLDER_LIST_OWNER_COLUMN}>Người soạn</span>
        <FolderSortButton
          label="Ngày tạo"
          field={DOCUMENT_SORT_FIELD.createdAt}
          activeField={sortField}
          dir={sortDir}
          onSortFieldChange={onSortFieldChange}
          onToggleSortDir={onToggleSortDir}
        />
        <span>Trạng thái</span>
        <span aria-hidden />
      </div>

      {/* `divide-y` ở khung chứa chứ không `border-b` + `last:border-b-0` trên dòng: mỗi
          dòng nằm trong vỏ `div.relative` của menu chuột phải nên `last:` không bao giờ
          trúng, dòng cuối ra hai nét viền chồng lên viền khung. */}
      <div className="divide-y">
        {children.map((folder) => (
          <FolderListRow
            selectable={selectable}
            key={`folder-${folder.id}`}
            item={{ kind: 'folder', folder }}
            selected={selection.isSelected(folderItemKey('folder', folder.id))}
            isFullText={isFullText}
            sourceFolderId={sourceFolderId}
            onClick={(modifiers) =>
              selection.handleClick(folderItemKey('folder', folder.id), modifiers)
            }
            onOpen={() => onOpenFolder(folder.id)}
            onViewDetails={() => onViewFolderDetails(folder)}
            onRename={() => rowActions.setRenameTarget(folder)}
            onMoveTo={() => rowActions.setMoveTarget(folder)}
            onManagePermissions={() => rowActions.setShareTargetId(folder.id)}
            onRemove={() => void rowActions.requestDelete(folder)}
            dropHighlighted={dragOverFolderId === folder.id}
            onDragOverFolder={() => setDragOverFolderId(folder.id)}
            onDragLeaveFolder={() =>
              setDragOverFolderId((current) => (current === folder.id ? null : current))
            }
            onDropOnFolder={(payload, keepInSource) => {
              setDragOverFolderId(null)
              onDropOnFolder(folder.id, payload, keepInSource)
            }}
          />
        ))}

        {documents.map((document) => (
          <FolderListRow
            selectable={selectable}
            key={`document-${document.id}`}
            item={{ kind: 'document', document }}
            selected={selection.isSelected(folderItemKey('document', document.id))}
            isFullText={isFullText}
            sourceFolderId={sourceFolderId}
            onClick={(modifiers) =>
              selection.handleClick(folderItemKey('document', document.id), modifiers)
            }
            onOpen={() => onOpenDocument(document)}
            onViewDetails={() => onViewDocumentDetails(document)}
            onMoveTo={canWrite ? () => onMoveDocumentTo(document) : undefined}
            onManagePermissions={
              canWrite && onShareDocument ? () => onShareDocument(document) : undefined
            }
            onRemove={canDelete ? () => void onRemoveDocument(document) : undefined}
            canWriteDocument={canWrite}
            canDeleteDocument={canDelete}
          />
        ))}
      </div>

      <FolderRowActionDialogs actions={rowActions} onNavigateToFolder={onOpenFolder} />
    </div>
  )
}
