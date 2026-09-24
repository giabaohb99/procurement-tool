import { useState } from 'react'

import { useHasChanged } from '@/shared/hooks/use-has-changed'

/**
 * Thư mục đang mở hộp «Chia sẻ» (popup, đặc tả §C — chốt lead 23/09/2026: bỏ
 * tab «Phân quyền», ba lối vào — nút «Chia sẻ» ở thanh trên, mục «Chia sẻ…»
 * trong menu chuột phải, nút «Quản lý quyền» ở khung chi tiết — đều mở ĐÚNG
 * một hộp thoại `FolderShareDialog`).
 *
 * `openOnMount` giữ TƯƠNG THÍCH NGƯỢC với lối vào cũ từ cây bên trái
 * (`document-folder-page.tsx` → `FolderTreePanel` → `onOpenAccessTab`, vẫn
 * đặt `?tab=access` trên URL) — không sửa được các tệp đó (thuộc Agent A).
 * `folder-contents-panel.tsx` tự lo phần DỌN tham số `tab` khỏi URL bằng một
 * effect RIÊNG của nó; hook này chỉ mở dialog, đọc `openOnMount` NGAY TRONG
 * RENDER (không `useEffect`) — cùng mẫu `useHasChanged`/
 * `usePageResetOnFilterChange` của chính repo: `shareFolderId` là state CỤC
 * BỘ trong cùng cây hook, không đụng tới component khác.
 */
export function useFolderShareTarget(currentFolderId: number, openOnMount: boolean) {
  const [shareFolderId, setShareFolderId] = useState<number | null>(null)

  if (useHasChanged(openOnMount) && openOnMount) {
    setShareFolderId(currentFolderId)
  }

  return {
    shareFolderId,
    openShare: (folderId: number = currentFolderId) => setShareFolderId(folderId),
    closeShare: () => setShareFolderId(null),
  }
}
