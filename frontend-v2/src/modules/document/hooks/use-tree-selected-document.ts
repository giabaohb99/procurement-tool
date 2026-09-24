import { useState } from 'react'

import { folderItemDomId, folderItemKey } from '../helpers/folder-item-id'
import type { DocumentRecord } from '../types/document-record'
import type { useFolderContentSelection } from './use-folder-content-selection'

interface UseTreeSelectedDocumentOptions {
  /** Văn bản CÂY bên trái vừa chỉ tới (bấm một lá) — `null`/`undefined` = không có gì đang chờ. */
  selectedDocumentId: number | null | undefined
  isLoading: boolean
  rows: readonly DocumentRecord[]
  selection: ReturnType<typeof useFolderContentSelection>
  /** Tìm thấy văn bản trong trang đang nạp — mở khung chi tiết (nơi gọi tự quyết định cách mở). */
  onFound: () => void
  /** Đã XỬ LÝ XONG (tìm thấy hoặc không) — trang cha xóa `?doc=` khỏi URL. */
  onHandled?: () => void
}

/**
 * Chọn + cuộn tới ĐÚNG dòng khi văn bản được CÂY bên trái chỉ tới (đặc tả §3,
 * duoc-CR-476) — tách khỏi `folder-documents-table.tsx` để tệp đó dưới 200
 * dòng. Chạy NGAY TRONG RENDER (không `useEffect`, cùng mẫu chính thức
 * `useHasChanged` của repo) vì phải đợi trang tài liệu NẠP XONG rồi mới tìm
 * (nạp dở mà tìm ngay thì không thấy, tưởng văn bản không có ở đây).
 *
 * ⚠️ Không tìm thấy (trang khác/đã bị gỡ) VẪN PHẢI báo `onHandled` — không thì
 * `?doc=` treo mãi trên URL, ép mọi lượt chọn KHÁC ở khung phải quay lại đúng
 * văn bản đó.
 */
export function useTreeSelectedDocument({
  selectedDocumentId,
  isLoading,
  rows,
  selection,
  onFound,
  onHandled,
}: UseTreeSelectedDocumentOptions) {
  const signature = `${selectedDocumentId ?? ''}:${isLoading}`
  const [lastHandledSignature, setLastHandledSignature] = useState<string | null>(null)

  if (selectedDocumentId != null && !isLoading && signature !== lastHandledSignature) {
    setLastHandledSignature(signature)
    const target = rows.find((row) => row.id === selectedDocumentId)
    if (target) {
      selection.selectOnly(folderItemKey('document', target.id))
      onFound()
      window.requestAnimationFrame(() => {
        document.getElementById(folderItemDomId('document', target.id))?.scrollIntoView({ block: 'center' })
      })
    }
    onHandled?.()
  }
}
