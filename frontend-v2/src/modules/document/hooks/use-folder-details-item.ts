import { parseFolderItemKey } from '../helpers/folder-item-id'
import { useDocFolder } from './use-document-folders'
import type { FolderDetailsPanelItem } from '../components/folder-details-panel'
import type { DocFolderDetail } from '../types/document-folder'
import type { DocumentRecord } from '../types/document-record'

/**
 * Mục đang hiện trong khung chi tiết — suy từ lựa chọn hiện tại của
 * `useFolderContentSelection`. Tách khỏi `folder-documents-table.tsx` để tệp
 * đó dưới 200 dòng.
 *
 * KHÔNG lộ dữ liệu chưa nạp: thư mục CON được chọn phải tự đi lấy chi tiết
 * ĐẦY ĐỦ của đúng nó qua `useDocFolder` — tái dùng `DocFolderTreeNode` cụt
 * (thiếu `effective_access`) sẽ đọc nhầm thành "chưa ai có quyền" trong khi
 * đó chỉ là CHƯA NẠP, không phải sự thật.
 */
export function useFolderDetailsItem(
  selectedKeys: Set<string>,
  currentFolder: DocFolderDetail | undefined,
  rows: readonly DocumentRecord[],
): FolderDetailsPanelItem {
  const selectedArr = Array.from(selectedKeys)
  const singleSelected = selectedArr.length === 1 ? parseFolderItemKey(selectedArr[0]) : null
  const { data: selectedChildFolder } = useDocFolder(
    singleSelected?.kind === 'folder' ? singleSelected.id : undefined,
  )

  if (selectedArr.length === 0) return currentFolder ? { kind: 'folder', folder: currentFolder } : { kind: 'none' }
  if (selectedArr.length > 1) return { kind: 'multiple', count: selectedArr.length }
  if (singleSelected?.kind === 'folder') {
    return selectedChildFolder ? { kind: 'folder', folder: selectedChildFolder } : { kind: 'none' }
  }
  const document = rows.find((row) => row.id === singleSelected?.id)
  return document ? { kind: 'document', document } : { kind: 'none' }
}
