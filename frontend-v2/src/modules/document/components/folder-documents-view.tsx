import { useState, type ReactNode } from 'react'

import { DataTablePagination } from '@/shared/data-table/data-table-pagination'
import { FolderDocumentsFilterToolbar } from './folder-documents-filter-toolbar'
import { FolderEmptyState } from './folder-empty-state'
import { DocumentShareDialog } from './document-share-dialog'
import { FolderGridView } from './folder-grid-view'
import { FolderListView } from './folder-list-view'
import { FolderSortButton } from './folder-sort-button'
import type { FolderDragPayload } from '../helpers/folder-drag-payload'
import { folderItemKey } from '../helpers/folder-item-id'
import {
  DOCUMENT_SORT_FIELD,
  type DocumentSortField,
  type SortDirection,
} from '../helpers/sort-document-rows'
import type { useFolderContentSelection } from '../hooks/use-folder-content-selection'
import type { useFolderDocumentsQuery } from '../hooks/use-folder-documents-query'
import type { DocFolderTreeNode } from '../types/document-folder'
import type { DocumentRecord } from '../types/document-record'
import type { DocumentType } from '../types/document-type'

interface FolderDocumentsViewProps {
  isGrid: boolean
  folderId: number
  q: ReturnType<typeof useFolderDocumentsQuery>
  documentTypes: DocumentType[]
  /**
   * Thanh thao tác hàng loạt (`FolderSelectionToolbar`) khi ĐANG có lượt chọn
   * — THAY chỗ hàng tìm/lọc (đặc tả §B, phản hồi 24/09/2026: kiểu Drive, một
   * hàng chỉ hiện MỘT thứ tại một thời điểm) thay vì xếp chồng lên trên như
   * bản cũ. `null` = không có gì chọn, hiện hàng tìm/lọc như thường.
   */
  selectionToolbar: ReactNode
  /** Khối thẻ THƯ MỤC CON của chế độ Lưới — vẽ ngay DƯỚI hàng tìm/lọc. `null` = không có. */
  folderCards?: ReactNode
  sortField: DocumentSortField
  sortDir: SortDirection
  onSortFieldChange: (field: DocumentSortField) => void
  onToggleSortDir: () => void
  selection: ReturnType<typeof useFolderContentSelection>
  onOpenDocument: (document: DocumentRecord) => void
  onViewDetails: (document: DocumentRecord) => void
  onRemoveDocument: (document: DocumentRecord) => void
  canWrite: boolean
  canDelete: boolean
  /** Thư mục CON hiện ở chế độ Danh sách (GỘP vào cùng bảng với văn bản) — chế độ Lưới rỗng, `folder-documents-table.tsx` tự vẽ khối thẻ riêng. */
  children: DocFolderTreeNode[]
  onOpenFolder: (id: number) => void
  onViewFolderDetails: (folder: DocFolderTreeNode) => void
  onDropOnFolder: (
    targetFolderId: number,
    payload: FolderDragPayload,
    keepInSource: boolean,
  ) => void
}

/**
 * Khối «Văn bản» của khung nội dung — Hàng 2 (tìm/lọc, đặc tả A phản hồi
 * 24/09/2026: bỏ nhãn «Văn bản», bỏ ô sắp xếp Select — sắp xếp nay bấm THẲNG
 * cột (Danh sách, `folder-list-view.tsx`) hoặc nhãn nhỏ phía trên (Lưới)) +
 * chế độ Lưới/Danh sách. Tự dựng `filterToolbar` MỘT LẦN rồi dùng NGUYÊN XI
 * cho cả hai chế độ (bug lead bắt 23/09/2026: trước đây Lưới không có khung
 * bọc nên mỗi ô lọc rớt một dòng).
 */
export function FolderDocumentsView({
  isGrid,
  folderId,
  q,
  documentTypes,
  selectionToolbar,
  folderCards,
  sortField,
  sortDir,
  onSortFieldChange,
  onToggleSortDir,
  selection,
  onOpenDocument,
  onViewDetails,
  onRemoveDocument,
  canWrite,
  canDelete,
  children,
  onOpenFolder,
  onViewFolderDetails,
  onDropOnFolder,
}: FolderDocumentsViewProps) {
  //  Văn bản đang mở hộp «Chia sẻ» (menu ⋮ / chuột phải / nút chia sẻ trên dòng).
  const [shareDocument, setShareDocument] = useState<DocumentRecord | null>(null)
  const filterToolbar = (
    <FolderDocumentsFilterToolbar
      keyword={q.keyword}
      onKeywordChange={q.setKeyword}
      documentTypes={documentTypes}
      typeId={q.typeId}
      onTypeIdChange={q.setTypeId}
      status={q.status}
      onStatusChange={q.setStatus}
      year={q.year}
      onYearChange={q.setYear}
      includeSubfolders={q.includeSubfolders}
      onIncludeSubfoldersChange={q.setIncludeSubfolders}
    />
  )

  const hasDocuments = q.rows.length > 0
  //  Chế độ Lưới truyền `children=[]` (thư mục con vẽ riêng ở `folderCards`),
  //  nên phải hỏi CẢ `folderCards` — thiếu vế đó thì thư mục chỉ chứa thư mục
  //  con vẫn hiện «Thư mục này chưa có gì» ngay dưới 14 thẻ thư mục (lỗi lead
  //  chụp 24/09/2026).
  const hasFolders = children.length > 0 || Boolean(folderCards)
  const isEmpty = !hasFolders && !hasDocuments
  //  ĐANG LỌC/TÌM (kể cả gõ chưa đủ ký tự) ≠ THƯ MỤC RỖNG — hai câu chuyện
  //  khác nhau, đè chung một thông báo là sai (chốt dọn gọn lead 24/09/2026
  //  tối, hạng mục §2): lọc ra 0 kết quả thì vẫn còn chữ trong ô tìm, "Tạo thư
  //  mục" không giải quyết gì cả.
  const isFiltering = q.filtersActive || q.keyword.trim().length > 0
  const filteredEmptyMessage = q.isFullText
    ? 'Không tìm thấy văn bản nào khớp câu tìm — trong tên, số hiệu, nội dung lẫn tệp đính kèm.'
    : 'Không có văn bản nào khớp điều kiện đang lọc.'

  return (
    <div className="space-y-1.5">
      {selectionToolbar ?? filterToolbar}

      {isGrid && folderCards && <div className="pt-1.5">{folderCards}</div>}

      {/*  Lưới: hàng sắp xếp + lưới văn bản CHỈ dựng khi có văn bản — thư mục
          chỉ chứa thư mục con thì dừng ở khối thẻ thư mục, kiểu Drive. */}
      {isGrid ? (
        hasDocuments && (
          <>
            {/*  Nhãn sắp xếp nhỏ kiểu Drive, thay Select + nút đổi chiều cũ. */}
            <div className="flex items-center gap-3 border-b pb-1.5 text-xs">
              <FolderSortButton
                label="Tên"
                field={DOCUMENT_SORT_FIELD.name}
                activeField={sortField}
                dir={sortDir}
                onSortFieldChange={onSortFieldChange}
                onToggleSortDir={onToggleSortDir}
              />
              <FolderSortButton
                label="Loại"
                field={DOCUMENT_SORT_FIELD.type}
                activeField={sortField}
                dir={sortDir}
                onSortFieldChange={onSortFieldChange}
                onToggleSortDir={onToggleSortDir}
              />
              <FolderSortButton
                label="Ngày tạo"
                field={DOCUMENT_SORT_FIELD.createdAt}
                activeField={sortField}
                dir={sortDir}
                onSortFieldChange={onSortFieldChange}
                onToggleSortDir={onToggleSortDir}
              />
            </div>
            <FolderGridView
              documents={q.rows}
              sourceFolderId={folderId}
              isSelected={selection.isSelected}
              onItemClick={(id, modifiers) =>
                selection.handleClick(folderItemKey('document', id), modifiers)
              }
              onOpen={onOpenDocument}
              onViewDetails={onViewDetails}
              onMoveTo={(document) => selection.selectOnly(folderItemKey('document', document.id))}
              onShare={setShareDocument}
              onRemove={(document) => void onRemoveDocument(document)}
              canWrite={canWrite}
              canDelete={canDelete}
            />
          </>
        )
      ) : (
        <FolderListView
          children={children}
          documents={q.rows}
          sourceFolderId={folderId}
          isFullText={q.isFullText}
          sortField={sortField}
          sortDir={sortDir}
          onSortFieldChange={onSortFieldChange}
          onToggleSortDir={onToggleSortDir}
          selection={selection}
          onOpenFolder={onOpenFolder}
          onOpenDocument={onOpenDocument}
          onViewFolderDetails={onViewFolderDetails}
          onViewDocumentDetails={onViewDetails}
          onDropOnFolder={onDropOnFolder}
          onMoveDocumentTo={(document) =>
            selection.selectOnly(folderItemKey('document', document.id))
          }
          onShareDocument={setShareDocument}
          onRemoveDocument={onRemoveDocument}
          canWrite={canWrite}
          canDelete={canDelete}
        />
      )}

      {!q.isLoading && !hasDocuments && isFiltering && (
        <p className="py-8 text-center text-sm text-muted-foreground">{filteredEmptyMessage}</p>
      )}
      {!q.isLoading && isEmpty && !isFiltering && <FolderEmptyState />}

      {shareDocument && (
        <DocumentShareDialog
          document={shareDocument}
          open
          onOpenChange={(open) => !open && setShareDocument(null)}
        />
      )}

      <DataTablePagination
        page={q.page}
        pageSize={q.pageSize}
        total={q.total}
        onPageChange={q.setPage}
        onPageSizeChange={q.setPageSize}
        unitLabel="văn bản"
      />
    </div>
  )
}
