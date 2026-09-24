import { useMemo } from 'react'

import { filterTree } from '@/shared/tree/filter-tree'
import { buildFolderTree } from '../helpers/build-folder-tree'
import { folderNameMatches } from '../helpers/folder-tree-search'
import { insertFolderDocumentLeaves } from '../helpers/insert-folder-document-leaves'
import { insertTempChildNode, NEW_FOLDER_TEMP_ID } from '../helpers/insert-temp-tree-node'
import type { DocFolderTreeNode } from '../types/document-folder'
import { useFolderTreeDocumentLeaves } from './use-folder-tree-document-leaves'

interface UseFolderTreeNodesOptions {
  rows: DocFolderTreeNode[] | undefined
  keyword: string
  expandedIds: ReadonlySet<string | number>
  creatingUnder: { parentId: number } | null
  selectedFolderId: number | null
  /** «Hiện văn bản trong cây» (duoc-CR-476) — `false` thì KHÔNG gọi nạp lá văn bản cho bất kỳ thư mục nào, kể cả đang mở. */
  showDocuments: boolean
}

/**
 * Gộp BỐN bước dựng cây hiển thị (build → lọc từ khóa → chèn dòng tạm «thư
 * mục mới» → chèn lá văn bản của thư mục đang mở) thành MỘT hook, để
 * `folder-tree-panel.tsx` chỉ còn lo tiêu đề + ô tìm + gắn props vào
 * `TreeView`. Tách riêng vì bốn bước này giờ đã kéo theo một `useQueries`
 * (nạp lá văn bản) — nhét thẳng vào component thì tệp đó vượt 200 dòng.
 */
export function useFolderTreeNodes({
  rows,
  keyword,
  expandedIds,
  creatingUnder,
  selectedFolderId,
  showDocuments,
}: UseFolderTreeNodesOptions) {
  const fullTree = useMemo(() => buildFolderTree(rows ?? []), [rows])
  const { nodes: filteredTree, matchedIds } = useMemo(
    () => filterTree(fullTree, (node) => folderNameMatches(node.label, keyword)),
    [fullTree, keyword],
  )
  //  Tooltip (`buildFolderTooltip`) cần TRA NGƯỢC tổ tiên theo `parent_id` —
  //  dùng `rows` PHẲNG gốc (không phải `fullTree` đã lồng nhau) cho gọn.
  const rowsById = useMemo(() => new Map((rows ?? []).map((row) => [row.id, row])), [rows])

  //  Lá văn bản chỉ nạp cho thư mục THẬT đang mở (id số) — dòng tạm «thư mục
  //  mới» mang id chuỗi (`NEW_FOLDER_TEMP_ID`), không bao giờ lọt vào đây.
  //  `showDocuments = false` → mảng RỖNG, tức `useFolderTreeDocumentLeaves`
  //  không gọi API nào cả (yêu cầu §2, duoc-CR-476: tắt công tắc thì KHÔNG
  //  được âm thầm vẫn nạp rồi lọc ở client).
  const expandedFolderIds = useMemo(
    () =>
      showDocuments
        ? Array.from(expandedIds).filter((id): id is number => typeof id === 'number')
        : [],
    [expandedIds, showDocuments],
  )
  const leavesByFolderId = useFolderTreeDocumentLeaves(expandedFolderIds)
  //  Tập id dùng để CHÈN LÁ — khác `expandedIds` (dùng để vẽ chevron mở/đóng
  //  thư mục CON thật): tắt «Hiện văn bản trong cây» thì tập này RỖNG nên
  //  `insertFolderDocumentLeaves` không chèn dòng «Đang tải…»/«(trống)» nào,
  //  dù thư mục vẫn đang mở trên cây.
  const leafExpandedIds = useMemo(() => new Set(expandedFolderIds), [expandedFolderIds])

  const withTemp = creatingUnder ? insertTempChildNode(filteredTree, creatingUnder.parentId) : filteredTree
  const { tree: visibleTree, leaves } = insertFolderDocumentLeaves(withTemp, leafExpandedIds, leavesByFolderId)

  const effectiveSelectedId = creatingUnder ? NEW_FOLDER_TEMP_ID : selectedFolderId

  return { visibleTree, leaves, matchedIds, rowsById, effectiveSelectedId }
}
