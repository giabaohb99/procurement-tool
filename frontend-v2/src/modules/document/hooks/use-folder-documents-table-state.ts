import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { usePersistedToggle } from '@/shared/hooks/use-persisted-toggle'
import { folderItemKey, splitFolderItemKeys } from '../helpers/folder-item-id'
import { FOLDER_VIEW_STORAGE_KEY } from '../helpers/folder-view-storage-key'
import { DOCUMENT_SORT_FIELD, type DocumentSortField, type SortDirection } from '../helpers/sort-document-rows'
import { useActiveDocumentTypes } from './use-document-types'
import { useDocFolder, useDocFolderTree } from './use-document-folders'
import { useFolderContentSelection } from './use-folder-content-selection'
import { useFolderDetailsItem } from './use-folder-details-item'
import { useFolderDocumentsQuery } from './use-folder-documents-query'
import { useFolderDropActions } from './use-folder-drop-actions'
import { useFolderShareTarget } from './use-folder-share-target'
import { useTreeSelectedDocument } from './use-tree-selected-document'
import { canBulkSelectFolder } from '../types/document-folder'
import type { DocumentRecord } from '../types/document-record'

interface UseFolderDocumentsTableStateArgs {
  folderId: number
  folderName: string
  openShareOnMount: boolean
  selectedDocumentId?: number | null
  onDocumentHandled?: () => void
}

/**
 * TOÀN BỘ state/hook của `FolderDocumentsTable` (chế độ Lưới/Danh sách, sắp
 * xếp, khung chi tiết, hộp «Chia sẻ», truy vấn văn bản + thư mục con, chọn
 * kiểu Drive, kéo thả) — tách ra để `folder-documents-table.tsx` chỉ còn lo
 * BỐ CỤC + nối props, dưới 200 dòng (đúng đúng lời tệp đó tự ghi ở đầu).
 */
export function useFolderDocumentsTableState({
  folderId,
  folderName,
  openShareOnMount,
  selectedDocumentId,
  onDocumentHandled,
}: UseFolderDocumentsTableStateArgs) {
  const navigate = useNavigate()
  const [isGrid, flipGrid] = usePersistedToggle(FOLDER_VIEW_STORAGE_KEY, false)
  const [sortField, setSortField] = useState<DocumentSortField>(DOCUMENT_SORT_FIELD.name)
  const [sortDir, setSortDir] = useState<SortDirection>('asc')
  const [detailsOpen, setDetailsOpen] = useState(false)
  const { shareFolderId, openShare, closeShare } = useFolderShareTarget(folderId, openShareOnMount)

  const q = useFolderDocumentsQuery(folderId, sortField, sortDir)
  const documentTypes = useActiveDocumentTypes()
  //  Cùng khóa truy vấn với `folder-contents-panel.tsx` (đã nạp trước khi tệp
  //  này mount) — đọc lại đây để Hàng 1 có `display_name`/`my_level` mà không
  //  phải truyền lặp qua props.
  const { data: folder } = useDocFolder(folderId)
  const { data: allFolders } = useDocFolderTree()
  const children = useMemo(
    () => (allFolders ?? []).filter((row) => row.parent_id === folderId),
    [allFolders, folderId],
  )

  const selection = useFolderContentSelection({
    folderKeys: children.filter(canBulkSelectFolder).map((child) => folderItemKey('folder', child.id)),
    documentKeys: q.rows.map((row) => folderItemKey('document', row.id)),
    resetSignal: [q.filterSignature, q.page],
  })

  const { handleDropOnFolder, handleRemoveDocument } = useFolderDropActions(folderId, folderName)

  function openDocument(document: DocumentRecord) {
    navigate(appRoutes.document.documentDetail(document.id))
  }

  function viewFolderDetails(child: { id: number }) {
    selection.selectOnly(folderItemKey('folder', child.id))
    setDetailsOpen(true)
  }

  //  «Xem chi tiết» của văn bản = vào trang chi tiết (đại ca chốt 25/09/2026),
  //  không phải bật khung thông tin bên phải như với thư mục.
  function viewDocumentDetails(document: DocumentRecord) {
    openDocument(document)
  }

  useTreeSelectedDocument({
    selectedDocumentId,
    isLoading: q.isLoading,
    rows: q.rows,
    selection,
    onFound: () => setDetailsOpen(true),
    onHandled: onDocumentHandled,
  })

  const detailsItem = useFolderDetailsItem(selection.selectedIds, folder, q.rows)

  const { folderIds: selectedFolderIds, documentIds: selectedDocumentIds } = useMemo(
    () => splitFolderItemKeys(selection.selectedIds),
    [selection.selectedIds],
  )

  return {
    isGrid,
    flipGrid,
    sortField,
    setSortField,
    sortDir,
    setSortDir,
    detailsOpen,
    setDetailsOpen,
    shareFolderId,
    openShare,
    closeShare,
    q,
    documentTypes,
    folder,
    children,
    selection,
    handleDropOnFolder,
    openDocument,
    viewFolderDetails,
    viewDocumentDetails,
    handleRemoveDocument,
    detailsItem,
    selectedFolderIds,
    selectedDocumentIds,
    hasSelection: selectedFolderIds.length + selectedDocumentIds.length > 0,
  }
}
