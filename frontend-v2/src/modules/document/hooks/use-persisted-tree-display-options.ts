import { useCallback, useState } from 'react'

const ARCHIVED_STORAGE_KEY = 'erp.document.folders.tree-show-archived'
const DOCUMENTS_STORAGE_KEY = 'erp.document.folders.tree-show-documents'

function readBoolean(key: string, fallback: boolean): boolean {
  try {
    const raw = localStorage.getItem(key)
    return raw === null ? fallback : raw === '1'
  } catch {
    //  Trình duyệt chặn storage: vẫn dùng được, chỉ không nhớ sang phiên sau.
    return fallback
  }
}

function writeBoolean(key: string, value: boolean): void {
  try {
    localStorage.setItem(key, value ? '1' : '0')
  } catch {
    //  bỏ qua
  }
}

/**
 * Hai công tắc HIỂN THỊ của khung cây (menu `⋯` ở tiêu đề — yêu cầu đại ca
 * 23/09/2026 tối, duoc-CR-476): «Hiện thư mục ngừng dùng» và «Hiện văn bản
 * trong cây». Cả hai NHỚ qua `localStorage` — trước đây `includeArchived` chỉ
 * là một `useState` cục bộ trong `folder-tree-panel.tsx`, mất ngay khi rời
 * trang. Tách thành hook riêng để tệp đó giữ dưới 200 dòng.
 *
 * `showDocuments = false` nghĩa là CHỈ hiện thư mục — nơi gọi (`use-folder-tree-nodes.ts`)
 * đọc cờ này để KHÔNG gọi `useFolderTreeDocumentLeaves` (không tự nạp lá văn
 * bản), chứ không phải nạp xong rồi ẩn đi.
 */
export function usePersistedTreeDisplayOptions() {
  const [includeArchived, setIncludeArchivedState] = useState(() => readBoolean(ARCHIVED_STORAGE_KEY, false))
  const [showDocuments, setShowDocumentsState] = useState(() => readBoolean(DOCUMENTS_STORAGE_KEY, true))

  const setIncludeArchived = useCallback((value: boolean) => {
    setIncludeArchivedState(value)
    writeBoolean(ARCHIVED_STORAGE_KEY, value)
  }, [])

  const setShowDocuments = useCallback((value: boolean) => {
    setShowDocumentsState(value)
    writeBoolean(DOCUMENTS_STORAGE_KEY, value)
  }, [])

  return { includeArchived, setIncludeArchived, showDocuments, setShowDocuments }
}
