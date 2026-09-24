import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import type { RefObject } from 'react'

import { appRoutes } from '@/shared/constants/app-routes'
import type { TreeNode } from '@/shared/tree/tree-types'
import { ancestorIdsOfMatches } from '../helpers/folder-tree-search'
import type { FolderTreeLeafData } from '../helpers/insert-folder-document-leaves'
import { NEW_FOLDER_TEMP_ID } from '../helpers/insert-temp-tree-node'
import type { DocFolderTreeNode } from '../types/document-folder'

interface UseFolderTreeNavigationOptions {
  selectedFolderId: number | null
  rows: DocFolderTreeNode[] | undefined
  leaves: ReadonlyMap<string, FolderTreeLeafData>
  expandAncestors: (ancestorIds: (string | number)[]) => void
  expandedIds: ReadonlySet<string | number>
  scrollContainerRef: RefObject<HTMLDivElement | null>
  onSelectFolder: (id: number) => void
  onSelectDocument: (folderId: number, documentId: number) => void
}

/**
 * Đồng bộ CÂY ⇄ KHUNG NỘI DUNG + hai mức "bấm" của một dòng cây (đặc tả §3/§4,
 * duoc-CR-476, yêu cầu 23/09/2026 tối) — tách khỏi `folder-tree-panel.tsx` để
 * tệp đó dưới 200 dòng:
 *
 * 1. Thư mục ĐANG CHỌN đổi từ NGOÀI (bấm breadcrumb/thẻ ở khung phải, dán link
 *    `?folder=`…) → tự MỞ đủ tổ tiên + chính nó rồi CUỘN dòng đó vào tầm nhìn, để tô sáng
 *    (`selected`) không âm thầm nằm trong một nhánh đang gập.
 * 2. `handleSelect` (bấm thường/Ctrl+A…) CHỈ chọn — lá văn bản gọi
 *    `onSelectDocument` để khung phải tự mở + cuộn tới, KHÔNG điều hướng rời
 *    trang. `handleActivate` (Enter/Space) và `handleRowDoubleClick` (bấm đúp)
 *    mới thật sự MỞ (lá văn bản → trang chi tiết).
 */
export function useFolderTreeNavigation({
  selectedFolderId,
  rows,
  leaves,
  expandAncestors,
  expandedIds,
  scrollContainerRef,
  onSelectFolder,
  onSelectDocument,
}: UseFolderTreeNavigationOptions) {
  const navigate = useNavigate()

  useEffect(() => {
    if (selectedFolderId == null || !rows) return
    //  Mở tổ tiên VÀ CHÍNH thư mục đang chọn (chốt 24/09/2026: bấm một thư
    //  mục ở khung phải thì cây phải bung ra đúng thư mục đó, thấy luôn thư
    //  mục con + văn bản bên trong — trước đây chỉ mở tổ tiên, dòng được tô
    //  sáng nhưng vẫn gập).
    expandAncestors([...ancestorIdsOfMatches(rows, new Set([selectedFolderId])), selectedFolderId])
    // eslint-disable-next-line react-hooks/exhaustive-deps -- chỉ chạy lại khi thư mục ĐANG CHỌN đổi, không phải mỗi lần expandedIds đổi (mở/gập tay một nhánh không nên bị ghi đè)
  }, [selectedFolderId, rows])

  useEffect(() => {
    if (selectedFolderId == null) return
    //  Chạy SAU hiệu ứng mở tổ tiên ở trên (theo `expandedIds` — dòng chỉ thật
    //  sự có mặt trong DOM sau khi state đó cập nhật xong một lượt render).
    scrollContainerRef.current
      ?.querySelector('[role="treeitem"][aria-selected="true"]')
      ?.scrollIntoView({ block: 'nearest' })
  }, [selectedFolderId, expandedIds, scrollContainerRef])

  function handleSelect(node: TreeNode<DocFolderTreeNode>) {
    if (node.id === NEW_FOLDER_TEMP_ID) return
    const leaf = leaves.get(String(node.id))
    if (leaf) {
      if (leaf.type === 'document') onSelectDocument(leaf.folderId, leaf.document.id)
      else if (leaf.type === 'more') onSelectFolder(leaf.folderId)
      return
    }
    onSelectFolder(Number(node.id))
  }

  function handleActivate(node: TreeNode<DocFolderTreeNode>) {
    const leaf = leaves.get(String(node.id))
    if (leaf?.type === 'document') {
      navigate(appRoutes.document.documentDetail(leaf.document.id))
      return
    }
    handleSelect(node)
  }

  function handleRowDoubleClick(
    node: TreeNode<DocFolderTreeNode>,
    canStartRename: (data: DocFolderTreeNode) => boolean,
    onRename: (data: DocFolderTreeNode) => void,
  ) {
    const leaf = leaves.get(String(node.id))
    if (leaf?.type === 'document') {
      navigate(appRoutes.document.documentDetail(leaf.document.id))
      return
    }
    if (node.data && canStartRename(node.data)) onRename(node.data)
  }

  return { handleSelect, handleActivate, handleRowDoubleClick }
}
